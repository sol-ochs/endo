# SQS Queue for Data Processing
resource "aws_sqs_queue" "data_processing_dlq" {
  name                      = "${var.project_name}-data-processing-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name        = "${var.project_name}-data-processing-dlq-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "data_processing" {
  name                       = "${var.project_name}-data-processing-queue-${var.environment}"
  visibility_timeout_seconds = 300 # 5 minutes (match Lambda timeout)
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.data_processing_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-data-processing-queue-${var.environment}"
    Environment = var.environment
  }
}

# IAM Role for Data Processing Lambda
resource "aws_iam_role" "data_processing_lambda_role" {
  name = "${var.project_name}-data-processing-lambda-role-${var.environment}"

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
    Name        = "${var.project_name}-data-processing-lambda-role-${var.environment}"
    Environment = var.environment
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "data_processing_lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.data_processing_lambda_role.name
}

# DynamoDB access policy for data processing
resource "aws_iam_role_policy" "data_processing_dynamodb_policy" {
  name = "${var.project_name}-data-processing-dynamodb-policy-${var.environment}"
  role = aws_iam_role.data_processing_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.users.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.glucose_insights.arn
      }
    ]
  })
}

# S3 access policy for data processing (read-only from glucose data bucket)
resource "aws_iam_role_policy" "data_processing_s3_policy" {
  name = "${var.project_name}-data-processing-s3-policy-${var.environment}"
  role = aws_iam_role.data_processing_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.glucose_data.arn,
          "${aws_s3_bucket.glucose_data.arn}/*"
        ]
      }
    ]
  })
}

# SQS access policy for data processing
resource "aws_iam_role_policy" "data_processing_sqs_policy" {
  name = "${var.project_name}-data-processing-sqs-policy-${var.environment}"
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
        Resource = aws_sqs_queue.data_processing.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.data_processing.arn
      }
    ]
  })
}

# Coordinator Lambda Function
data "archive_file" "data_coordinator_lambda" {
  type        = "zip"
  source_file = "../data-processing/coordinator/lambda_function.py"
  output_path = "../data-processing/coordinator/coordinator.zip"
}

resource "aws_lambda_function" "data_processing_coordinator" {
  filename         = data.archive_file.data_coordinator_lambda.output_path
  function_name    = "${var.project_name}-data-processing-coordinator-${var.environment}"
  role            = aws_iam_role.data_processing_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256
  source_code_hash = data.archive_file.data_coordinator_lambda.output_base64sha256

  environment {
    variables = {
      USERS_TABLE   = aws_dynamodb_table.users.name
      SQS_QUEUE_URL = aws_sqs_queue.data_processing.url
      LOG_LEVEL     = var.environment == "dev" ? "DEBUG" : "INFO"
    }
  }

  tags = {
    Name        = "${var.project_name}-data-processing-coordinator-${var.environment}"
    Environment = var.environment
  }
}

# Processor Lambda Function
data "archive_file" "data_processor_lambda" {
  type        = "zip"
  source_dir  = "../data-processing/processor"
  output_path = "../data-processing/processor/processor.zip"
}

resource "aws_lambda_function" "data_processor" {
  filename                       = data.archive_file.data_processor_lambda.output_path
  function_name                  = "${var.project_name}-data-processor-${var.environment}"
  role                          = aws_iam_role.data_processing_lambda_role.arn
  handler                       = "lambda_function.lambda_handler"
  runtime                       = "python3.11"
  timeout                       = 300 # 5 minutes
  memory_size                   = 512
  reserved_concurrent_executions = 10
  source_code_hash              = data.archive_file.data_processor_lambda.output_base64sha256

  layers = [
    aws_lambda_layer_version.shared_layer.arn
  ]

  environment {
    variables = {
      S3_BUCKET_NAME         = aws_s3_bucket.glucose_data.bucket
      GLUCOSE_INSIGHTS_TABLE = aws_dynamodb_table.glucose_insights.name
      LOG_LEVEL              = var.environment == "dev" ? "DEBUG" : "INFO"
    }
  }

  tags = {
    Name        = "${var.project_name}-data-processor-${var.environment}"
    Environment = var.environment
  }
}

# SQS trigger for Processor Lambda
resource "aws_lambda_event_source_mapping" "data_processing_sqs_trigger" {
  event_source_arn = aws_sqs_queue.data_processing.arn
  function_name    = aws_lambda_function.data_processor.arn
  batch_size       = 1
  enabled          = true
}

# EventBridge Schedule for Weekly Processing
# Runs every Sunday at midnight UTC
resource "aws_cloudwatch_event_rule" "weekly_processing" {
  name                = "${var.project_name}-data-processing-weekly-${var.environment}"
  description         = "Trigger data processing coordinator every Sunday at midnight UTC"
  schedule_expression = "cron(0 0 ? * SUN *)"

  tags = {
    Name        = "${var.project_name}-data-processing-weekly-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "data_processing_coordinator_target" {
  rule      = aws_cloudwatch_event_rule.weekly_processing.name
  target_id = "DataProcessingCoordinator"
  arn       = aws_lambda_function.data_processing_coordinator.arn
}

# Permission for EventBridge to invoke Coordinator Lambda
resource "aws_lambda_permission" "allow_eventbridge_coordinator" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processing_coordinator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_processing.arn
}
