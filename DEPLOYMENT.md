# Deployment Guide

This guide will walk you through deploying the Endo application for development using AWS free tier resources.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with your credentials
3. **Terraform** installed (>= 1.0)
4. **Node.js** and **Python 3.9+** for local development

## Deployment Steps

### Step 1: Configure AWS Credentials

```bash
aws configure
# Follow prompts to set your Access Key, Secret Key, region, and output format
```

### Step 2: Deploy Infrastructure with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply
```

### Step 3: Set Up Environment Configuration

```bash
# Return to project root
cd ..

# Generate environment configuration from Terraform outputs
./scripts/setup-env.sh dev
```

### Step 4: Setup Backend (Python API)

```bash
cd user-management-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file ../.env.dev
```

### Step 5: Setup Frontend (React)

Open a new terminal and run:

```bash
cd ui

# Install dependencies
npm install

# Run the React development server (automatically loads ui/.env)
npm start
```

## Step 6: Test the Application

Open your browser and navigate to `http://localhost:3000`. You should see the Endo application running.

## Cost Monitoring

Monitor your AWS usage to stay within free tier limits:

1. **Cognito**: Free for up to 50,000 MAUs
2. **DynamoDB**: 25GB storage + 200M requests/month free
3. **Lambda**: 1M requests + 400K GB-seconds/month free

### Useful Commands

Check Terraform outputs:
```bash
cd terraform && terraform output
```

List DynamoDB tables:
```bash
aws dynamodb list-tables
```

List Cognito User Pools:
```bash
aws cognito-idp list-user-pools --max-results 10
```

## Cleanup

To destroy all AWS resources:

```bash
cd terraform
terraform destroy
```

**Warning**: This will permanently delete all data in your DynamoDB tables and remove your Cognito User Pool.