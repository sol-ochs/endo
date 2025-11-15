# DynamoDB table for users
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users-${var.environment}"
  billing_mode = "PAY_PER_REQUEST" # Free tier friendly
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # Global secondary index for email lookup
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-users-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# DynamoDB table for sessions
resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}-sessions-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  # TTL for automatic session cleanup
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-sessions-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# DynamoDB table for Dexcom credentials
resource "aws_dynamodb_table" "dexcom_credentials" {
  name         = "${var.project_name}-dexcom-credentials-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-dexcom-credentials-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# DynamoDB table for processed glucose insights
resource "aws_dynamodb_table" "glucose_insights" {
  name         = "${var.project_name}-glucose-insights-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "report_key"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "report_key"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-glucose-insights-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}