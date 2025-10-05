# Deployment Guide

## Prerequisites

- AWS Account with credentials configured (`aws configure`)
- Terraform >= 1.0
- Node.js and Python 3.9+

## Quick Start

**1. Deploy infrastructure**
```bash
cd terraform
cp dev.tfvars.example dev.tfvars  # First time only
terraform init # First time only
terraform apply -var-file="dev.tfvars"
```

**2. Generate environment files**
```bash
cd ..
./scripts/setup-env.sh dev
```

**3. Start backend**
```bash
cd user-management-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file ../.env.dev
```

**4. Start frontend** (new terminal)
```bash
cd ui
npm install
npm start
```

Open `http://localhost:3000`

## Cleanup

```bash
cd terraform
terraform destroy -var-file="dev.tfvars"
```