# Deployment Guide

Full AWS deployment for dev and prod environments.

## Prerequisites

- AWS Account with credentials configured (`aws configure`)
- Terraform >= 1.0

## Deploy Infrastructure

**1. Initialize and apply Terraform**
```bash
cd terraform
cp dev.tfvars.example dev.tfvars  # First time only
terraform init                    # First time only
terraform apply -var-file="dev.tfvars"
```

This deploys:
- EC2 instance (t3.micro) running the FastAPI backend in Docker
- Cognito user pool for authentication
- DynamoDB tables for data storage

**2. Get deployment outputs**
```bash
terraform output
```

Note the `api_url` - you'll need this for the frontend.

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