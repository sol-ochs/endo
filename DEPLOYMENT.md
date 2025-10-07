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

**2. Initialize and apply Terraform**
```bash
cd terraform
cp dev.tfvars.example dev.tfvars  # First time only
terraform init                     # First time only
terraform apply -var-file="dev.tfvars"
```

This deploys:
- Lambda function running the FastAPI backend
- API Gateway HTTP API
- Cognito user pool for authentication
- DynamoDB tables for data storage

**3. Get deployment outputs**
```bash
terraform output
```

Note the `api_url` - this is your backend API endpoint.

## Update Lambda Code

After making code changes:

```bash
# Re-package Lambda
./scripts/package-lambda.sh

# Deploy updated function
cd terraform
terraform apply -var-file="dev.tfvars"
```

## Environments

- **Dev**: `terraform apply -var-file="dev.tfvars"`
- **Prod**: `terraform apply -var-file="prod.tfvars"` (create as needed)

## Frontend Deployment

WIP - See [ui/README.md](ui/README.md) for local development.

## Local Development

To develop components locally against deployed infrastructure:
- **Backend**: See [user-management-api/README.md](user-management-api/README.md)
- **Frontend**: See [ui/README.md](ui/README.md)

## Cleanup

```bash
cd terraform
terraform destroy -var-file="dev.tfvars"
```