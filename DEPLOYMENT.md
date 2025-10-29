# Deployment Guide

Full AWS deployment for dev and prod environments using Lambda (free tier eligible).

## Prerequisites

- AWS Account with credentials configured (`aws configure`)
- Terraform >= 1.0
- Python 3.11+

## Deploy Infrastructure

**1. Package Lambda function**

```bash
./scripts/package-lambda.sh
```

This creates `user-management-api/lambda-package/deployment.zip` with your code and dependencies.

**2. Apply Terraform**

```bash
cd terraform
cp dev.tfvars.example dev.tfvars  # First time only
terraform init                    # First time only
terraform apply -var-file="dev.tfvars"
```

This deploys:
- Lambda function running the FastAPI backend
- API Gateway
- Cognito user pool
- DynamoDB tables

## Deploy Frontend to CloudFront

**Build and deploy the UI to S3/CloudFront:**

```bash
./scripts/deploy-ui.sh
```

The script will:
- Get the API URL from Terraform
- Build the React app with production optimizations and injected API URL
- Upload files to S3 with proper caching headers
- Invalidate CloudFront cache
- Display the CloudFront URL where your app is live

**Note**: The first deployment may take 10-15 minutes for CloudFront to fully distribute.

## Local Development

To run frontend locally:

```bash
cd ui
export REACT_APP_API_URL=$(cd ../terraform && terraform output -raw api_url)
npm start
```

This starts the dev server at http://localhost:3000

## Cleanup

```bash
cd terraform
terraform destroy -var-file="dev.tfvars"
```