# Deployment Guide

**Skip to:**
- [Local Development](#local-development) for daily feature work (local code + dev cloud resources)
- [Dev Deployment](#dev-deployment) for testing serverless in dev environment
- [Prod Deployment](#prod-deployment) for production release
- [Initial Setup](#initial-setup) if this is your first time

---

## Local Development

*Fast iteration with local backend + dev cloud database*

**Prerequisites:** Complete [Initial Setup](#initial-setup) for dev environment first.

### Setup Environment

```bash
# Generate environment files
./scripts/setup-env.sh local
```

### Run Backend

```bash
cd user-management-api

# Create virtual environment (first time only)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file ../.env.local
```

### Run Frontend

```bash
# In a new terminal
cd ui

# Install dependencies (first time only)
npm install

# Run the development server
npm start
```

The UI should be available at `http://localhost:3000`.

---

## Dev Deployment

*Test your serverless deployment in a dev environment*

**Prerequisites:** Complete [Initial Setup](#initial-setup) for dev environment first.

### Package and Deploy Lambda

```bash
# Package the backend
./scripts/package-lambda.sh

# Deploy Lambda function
cd terraform
terraform apply
cd ..
```

### Setup Environment

```bash
# Generate environment files for dev cloud backend
./scripts/setup-env.sh dev
```

### Run Frontend

```bash
cd ui

# Install dependencies (first time only)
npm install

# Run the development server (connects to API Gateway in dev)
npm start
```

Open `http://localhost:3000` in your browser.

---

## Prod Deployment

*Deploy to production environment*

**Prerequisites:** Complete [Initial Setup](#initial-setup) for prod environment first.

### Package and Deploy Lambda

```bash
# Package the backend
./scripts/package-lambda.sh

# Deploy to production
cd terraform
terraform workspace select prod  # or use -var="environment=prod"
terraform apply
cd ..
```

### Setup Environment

```bash
# Generate environment files for production
./scripts/setup-env.sh prod
```

### Deploy Frontend

See [Frontend Deployment](#frontend-deployment) section below for S3/CloudFront setup.

---

## Initial Setup

*Required AWS infrastructure setup (one-time per environment)*

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with your credentials
3. **Terraform** installed (>= 1.0)
4. **Node.js** and **Python 3.9+**

### Configure AWS

```bash
aws configure
# Enter your Access Key, Secret Key, region, and output format
```

### Deploy Dev Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan (defaults to dev environment)
terraform plan

# Deploy dev infrastructure (Cognito, DynamoDB, Lambda, API Gateway)
terraform apply
```

After this completes, continue to [Local Development](#local-development) or [Dev Deployment](#dev-deployment).

### Deploy Prod Infrastructure (when ready)

```bash
cd terraform

# Deploy prod infrastructure
terraform workspace new prod  # or use -var="environment=prod"
terraform plan
terraform apply
```

---

## Frontend Deployment

*Deploy React app to S3/CloudFront (coming soon)*

This section will contain instructions for deploying the frontend to S3 with CloudFront CDN.

---

## Useful Commands

**Switch between development modes:**
```bash
# Local development (local code + dev cloud)
./scripts/setup-env.sh local

# Dev cloud deployment
./scripts/setup-env.sh dev

# Prod cloud deployment
./scripts/setup-env.sh prod
```

**Check Terraform outputs:**
```bash
cd terraform && terraform output
```

**AWS resource commands:**
```bash
# List DynamoDB tables
aws dynamodb list-tables

# List Cognito User Pools
aws cognito-idp list-user-pools --max-results 10
```

---

## Cost Monitoring

Monitor your AWS usage to stay within free tier limits:

- **Cognito**: Free for up to 50,000 MAUs
- **DynamoDB**: 25GB storage + 200M requests/month free
- **Lambda**: 1M requests + 400K GB-seconds/month free
- **API Gateway**: 1M requests/month free

---

## Cleanup

To destroy all AWS resources in an environment:

```bash
cd terraform

# Destroy dev environment
terraform destroy

# Destroy prod environment
terraform workspace select prod
terraform destroy
```

**Warning**: This will permanently delete all data in your DynamoDB tables and remove your Cognito User Pool.