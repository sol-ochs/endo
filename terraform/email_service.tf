# SQS Queue for Email Service
resource "aws_sqs_queue" "email_service_dlq" {
  name                      = "${var.project_name}-email-service-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name        = "${var.project_name}-email-service-dlq-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "email_service" {
  name                       = "${var.project_name}-email-service-queue-${var.environment}"
  visibility_timeout_seconds = 300 # 5 minutes (match Lambda timeout)
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.email_service_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-email-service-queue-${var.environment}"
    Environment = var.environment
  }
}

# SES Email Identity
resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}

# IAM Role for Email Service Lambda
resource "aws_iam_role" "email_service_lambda_role" {
  name = "${var.project_name}-email-service-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-email-service-lambda-role-${var.environment}"
    Environment = var.environment
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "email_service_lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.email_service_lambda_role.name
}

# DynamoDB access policy for email service (read-only)
resource "aws_iam_role_policy" "email_service_dynamodb_policy" {
  name = "${var.project_name}-email-service-dynamodb-policy-${var.environment}"
  role = aws_iam_role.email_service_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.glucose_insights.arn
        ]
      }
    ]
  })
}

# SES send email policy
resource "aws_iam_role_policy" "email_service_ses_policy" {
  name = "${var.project_name}-email-service-ses-policy-${var.environment}"
  role = aws_iam_role.email_service_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.sender_email
          }
        }
      }
    ]
  })
}

# SQS access policy for email service
resource "aws_iam_role_policy" "email_service_sqs_policy" {
  name = "${var.project_name}-email-service-sqs-policy-${var.environment}"
  role = aws_iam_role.email_service_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.email_service.arn
      }
    ]
  })
}

# Email Sender Lambda Function
data "archive_file" "email_sender_lambda" {
  type        = "zip"
  source_dir  = "../email-service/sender"
  output_path = "../email-service/sender/sender.zip"
  excludes    = ["sender.zip", "__pycache__", "*.pyc", "email_template_fancy.py", "preview.html", "preview_template.py"]
}

resource "aws_lambda_function" "email_sender" {
  filename                       = data.archive_file.email_sender_lambda.output_path
  function_name                  = "${var.project_name}-email-sender-${var.environment}"
  role                          = aws_iam_role.email_service_lambda_role.arn
  handler                       = "lambda_function.lambda_handler"
  runtime                       = "python3.11"
  timeout                       = 60
  memory_size                   = 128
  reserved_concurrent_executions = 10
  source_code_hash              = data.archive_file.email_sender_lambda.output_base64sha256

  environment {
    variables = {
      GLUCOSE_INSIGHTS_TABLE = aws_dynamodb_table.glucose_insights.name
      USERS_TABLE            = aws_dynamodb_table.users.name
      SENDER_EMAIL           = var.sender_email
      FRONTEND_BASE_URL      = var.frontend_base_url
      LOG_LEVEL              = "INFO"
    }
  }

  tags = {
    Name        = "${var.project_name}-email-sender-${var.environment}"
    Environment = var.environment
  }
}

# SQS trigger for Email Sender Lambda
resource "aws_lambda_event_source_mapping" "email_service_sqs_trigger" {
  event_source_arn = aws_sqs_queue.email_service.arn
  function_name    = aws_lambda_function.email_sender.arn
  batch_size       = 1
  enabled          = true
}

# CloudWatch Log Group for Email Sender Lambda
resource "aws_cloudwatch_log_group" "email_sender_logs" {
  name              = "/aws/lambda/${aws_lambda_function.email_sender.function_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.project_name}-email-sender-logs-${var.environment}"
    Environment = var.environment
  }
}

# Update data processing Lambda to have SQS send permissions
resource "aws_iam_role_policy" "data_processing_email_queue_policy" {
  name = "${var.project_name}-data-processing-email-queue-policy-${var.environment}"
  role = aws_iam_role.data_processing_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ]
        Resource = aws_sqs_queue.email_service.arn
      }
    ]
  })
}
