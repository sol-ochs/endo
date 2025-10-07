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

## Start frontend

In another terminal:

```bash
cd ui && npm start
```

## Cleanup

```bash
cd terraform
terraform destroy -var-file="dev.tfvars"
```