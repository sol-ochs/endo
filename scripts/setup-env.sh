#!/bin/bash

# Script to set up environment configuration from Terraform outputs
# Usage: ./scripts/setup-env.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
TERRAFORM_DIR="./terraform"
ENV_FILE=".env.${ENVIRONMENT}"

echo "Setting up environment configuration for: $ENVIRONMENT"

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "Error: Terraform directory not found at $TERRAFORM_DIR"
    exit 1
fi

# Check if terraform has been applied
cd "$TERRAFORM_DIR"
if [ ! -f "terraform.tfstate" ]; then
    echo "Error: Terraform state not found. Please run 'terraform apply' first."
    exit 1
fi

echo "Fetching Terraform outputs..."

# Get terraform outputs
USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
CLIENT_ID=$(terraform output -raw cognito_client_id)
CLIENT_SECRET=$(terraform output -raw cognito_client_secret)
DOMAIN_URL=$(terraform output -raw cognito_domain_url)
USERS_TABLE=$(terraform output -raw dynamodb_users_table_name)
SESSIONS_TABLE=$(terraform output -raw dynamodb_sessions_table_name)
AWS_REGION=$(terraform output -raw aws_region)

cd ..

echo "Creating $ENV_FILE..."

# Create environment file
# Capitalize first letter of environment for display
ENV_DISPLAY=$(echo "$ENVIRONMENT" | sed 's/./\U&/')

cat > "$ENV_FILE" << EOF
# ${ENV_DISPLAY} Environment Configuration
# Generated automatically from Terraform outputs on $(date '+%Y-%m-%d')

# Application Environment
ENVIRONMENT=$ENVIRONMENT
NODE_ENV=$([ "$ENVIRONMENT" = "prod" ] && echo "production" || echo "development")

# AWS Configuration
AWS_REGION=$AWS_REGION

# Cognito Configuration
COGNITO_REGION=$AWS_REGION
COGNITO_USER_POOL_ID=$USER_POOL_ID
COGNITO_CLIENT_ID=$CLIENT_ID
COGNITO_CLIENT_SECRET=$CLIENT_SECRET
COGNITO_DOMAIN_URL=$DOMAIN_URL

# DynamoDB Configuration
USERS_TABLE=$USERS_TABLE
SESSIONS_TABLE=$SESSIONS_TABLE

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Frontend Configuration
REACT_APP_API_URL=$([ "$ENVIRONMENT" = "prod" ] && echo "https://your-production-api-url.com" || echo "http://localhost:8000")
REACT_APP_COGNITO_REGION=$AWS_REGION
REACT_APP_COGNITO_USER_POOL_ID=$USER_POOL_ID
REACT_APP_COGNITO_CLIENT_ID=$CLIENT_ID

# Logging
LOG_LEVEL=$([ "$ENVIRONMENT" = "prod" ] && echo "INFO" || echo "DEBUG")
EOF

echo "✅ Environment file created: $ENV_FILE"

# Create frontend-specific environment file
FRONTEND_ENV_FILE="ui/.env"
echo "Creating $FRONTEND_ENV_FILE..."

cat > "$FRONTEND_ENV_FILE" << EOF
# Frontend Environment Configuration
# Generated automatically from Terraform outputs on $(date '+%Y-%m-%d')

# API Configuration
REACT_APP_API_URL=$([ "$ENVIRONMENT" = "prod" ] && echo "https://your-production-api-url.com" || echo "http://localhost:8000")

# Cognito Configuration
REACT_APP_COGNITO_REGION=$AWS_REGION
REACT_APP_COGNITO_USER_POOL_ID=$USER_POOL_ID
REACT_APP_COGNITO_CLIENT_ID=$CLIENT_ID
EOF

echo "✅ Frontend environment file created: $FRONTEND_ENV_FILE"
echo ""
echo "Next steps:"
echo "1. Review and customize environment files if needed"
echo "2. Set AWS credentials if not already configured"
echo "3. Run your applications:"
echo "   - Backend: uvicorn app.main:app --env-file $ENV_FILE"
echo "   - Frontend: npm start (will automatically load $FRONTEND_ENV_FILE)"
echo ""
echo "For AWS credentials, you can either:"
echo "- Use AWS CLI: aws configure"
echo "- Set environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
echo "- Use IAM roles (recommended for production)"