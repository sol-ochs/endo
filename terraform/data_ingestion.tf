# S3 Bucket for Glucose Data Storage
resource "aws_s3_bucket" "glucose_data" {
  bucket = "${var.project_name}-glucose-data-${var.environment}"

  tags = {
    Name        = "${var.project_name}-glucose-data-${var.environment}"
    Environment = var.environment
    Purpose     = "glucose-data-storage"
  }
}

resource "aws_s3_bucket_versioning" "glucose_data" {
  bucket = aws_s3_bucket.glucose_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "glucose_data" {
  bucket = aws_s3_bucket.glucose_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "glucose_data" {
  bucket = aws_s3_bucket.glucose_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# SQS Queue for Data Ingestion
resource "aws_sqs_queue" "data_ingestion_dlq" {
  name                      = "${var.project_name}-data-ingestion-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name        = "${var.project_name}-data-ingestion-dlq-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "data_ingestion" {
  name                       = "${var.project_name}-data-ingestion-queue-${var.environment}"
  visibility_timeout_seconds = 300 # 5 minutes (match Lambda timeout)
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.data_ingestion_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-data-ingestion-queue-${var.environment}"
    Environment = var.environment
  }
}

# Lambda Layer for Data Ingestion Dependencies
resource "aws_lambda_layer_version" "data_ingestion_layer" {
  filename            = "../data-ingestion/layer/requests-layer.zip"
  layer_name          = "${var.project_name}-requests-layer-${var.environment}"
  compatible_runtimes = ["python3.11"]
  source_code_hash    = filebase64sha256("../data-ingestion/layer/requests-layer.zip")

  description = "Shared dependencies for data ingestion: requests"
}

# IAM Role for Data Ingestion Lambdas
resource "aws_iam_role" "data_ingestion_lambda_role" {
  name = "${var.project_name}-data-ingestion-lambda-role-${var.environment}"

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
    Name        = "${var.project_name}-data-ingestion-lambda-role-${var.environment}"
    Environment = var.environment
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "data_ingestion_lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.data_ingestion_lambda_role.name
}

# DynamoDB access policy for data ingestion
resource "aws_iam_role_policy" "data_ingestion_dynamodb_policy" {
  name = "${var.project_name}-data-ingestion-dynamodb-policy-${var.environment}"
  role = aws_iam_role.data_ingestion_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.dexcom_credentials.arn,
          aws_dynamodb_table.users.arn
        ]
      }
    ]
  })
}

# S3 access policy for data ingestion
resource "aws_iam_role_policy" "data_ingestion_s3_policy" {
  name = "${var.project_name}-data-ingestion-s3-policy-${var.environment}"
  role = aws_iam_role.data_ingestion_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
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

# SQS access policy for data ingestion
resource "aws_iam_role_policy" "data_ingestion_sqs_policy" {
  name = "${var.project_name}-data-ingestion-sqs-policy-${var.environment}"
  role = aws_iam_role.data_ingestion_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl"
        ]
        Resource = aws_sqs_queue.data_ingestion.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.data_ingestion.arn
      }
    ]
  })
}

# Coordinator Lambda Function
data "archive_file" "coordinator_lambda" {
  type        = "zip"
  source_file = "../data-ingestion/coordinator/lambda_function.py"
  output_path = "../data-ingestion/coordinator/coordinator.zip"
}

resource "aws_lambda_function" "data_ingestion_coordinator" {
  filename         = data.archive_file.coordinator_lambda.output_path
  function_name    = "${var.project_name}-data-ingestion-coordinator-${var.environment}"
  role            = aws_iam_role.data_ingestion_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256
  source_code_hash = data.archive_file.coordinator_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.data_ingestion_layer.arn]

  environment {
    variables = {
      DEXCOM_CREDENTIALS_TABLE = aws_dynamodb_table.dexcom_credentials.name
      SQS_QUEUE_URL           = aws_sqs_queue.data_ingestion.url
      LOG_LEVEL               = "INFO"
    }
  }

  tags = {
    Name        = "${var.project_name}-data-ingestion-coordinator-${var.environment}"
    Environment = var.environment
  }
}

# Worker Lambda Function
data "archive_file" "worker_lambda" {
  type        = "zip"
  source_file = "../data-ingestion/worker/lambda_function.py"
  output_path = "../data-ingestion/worker/worker.zip"
}

resource "aws_lambda_function" "data_ingestion_worker" {
  filename                       = data.archive_file.worker_lambda.output_path
  function_name                  = "${var.project_name}-data-ingestion-worker-${var.environment}"
  role                          = aws_iam_role.data_ingestion_lambda_role.arn
  handler                       = "lambda_function.lambda_handler"
  runtime                       = "python3.11"
  timeout                       = 300 # 5 minutes
  memory_size                   = 512
  reserved_concurrent_executions = 10
  source_code_hash              = data.archive_file.worker_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.data_ingestion_layer.arn]

  environment {
    variables = {
      DEXCOM_API_BASE_URL         = var.dexcom_api_base_url
      DEXCOM_CLIENT_ID            = var.dexcom_client_id
      DEXCOM_CLIENT_SECRET        = var.dexcom_client_secret
      DEXCOM_CREDENTIALS_TABLE    = aws_dynamodb_table.dexcom_credentials.name
      S3_BUCKET_NAME              = aws_s3_bucket.glucose_data.bucket
      LOG_LEVEL                   = "INFO"
    }
  }

  tags = {
    Name        = "${var.project_name}-data-ingestion-worker-${var.environment}"
    Environment = var.environment
  }
}

# SQS trigger for Worker Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.data_ingestion.arn
  function_name    = aws_lambda_function.data_ingestion_worker.arn
  batch_size       = 1
  enabled          = true
}

# EventBridge Schedule for Daily Ingestion
resource "aws_cloudwatch_event_rule" "daily_ingestion" {
  name                = "${var.project_name}-data-ingestion-daily-${var.environment}"
  description         = "Trigger data ingestion coordinator daily at 6 AM UTC"
  schedule_expression = "cron(0 6 * * ? *)"

  tags = {
    Name        = "${var.project_name}-data-ingestion-daily-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "coordinator_target" {
  rule      = aws_cloudwatch_event_rule.daily_ingestion.name
  target_id = "DataIngestionCoordinator"
  arn       = aws_lambda_function.data_ingestion_coordinator.arn
}

# Permission for EventBridge to invoke Coordinator Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_ingestion_coordinator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ingestion.arn
}