# IAM role for Lambda execution
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-execution-role-${var.environment}"

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
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution_role.name
}

# IAM policy for DynamoDB access
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "${var.project_name}-lambda-dynamodb-policy-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.sessions.arn,
          "${aws_dynamodb_table.users.arn}/*",
          "${aws_dynamodb_table.sessions.arn}/*"
        ]
      }
    ]
  })
}

# IAM policy for Cognito access
resource "aws_iam_role_policy" "lambda_cognito_policy" {
  name = "${var.project_name}-lambda-cognito-policy-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminDeleteUser",
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:ListUsers",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminConfirmSignUp"
        ]
        Resource = aws_cognito_user_pool.main.arn
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "api" {
  filename         = var.lambda_zip_path
  function_name    = "${var.project_name}-api-${var.environment}"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      COGNITO_USER_POOL_ID  = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID     = aws_cognito_user_pool_client.main.id
      COGNITO_CLIENT_SECRET = aws_cognito_user_pool_client.main.client_secret
      COGNITO_REGION        = var.aws_region
      USERS_TABLE           = aws_dynamodb_table.users.name
      SESSIONS_TABLE        = aws_dynamodb_table.sessions.name
      LOG_LEVEL             = "DEBUG"
      ALLOWED_ORIGINS       = "http://localhost:3000"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_iam_role_policy.lambda_cognito_policy,
  ]
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 7
}