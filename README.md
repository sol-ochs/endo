# Endo

A proactive type 1 diabetes assistant.

The average diabetic sees their endocrinologist only 1-2 times a year. Endo aims to fill that gap with periodic "nudges," using your recent glucose data to generate timely insights and actionable recommendations between doctor visits.

## Architecture

### Current Components
- **Account Management** (`ui/` + `user-management-api/`)
  - React + TypeScript frontend on CloudFront/S3
  - FastAPI backend on Lambda
  - Cognito authentication with JWT tokens
  - Dexcom OAuth integration for connecting CGM accounts
- **Infrastructure** (`terraform/`)
  - Lambda + API Gateway + Cognito + DynamoDB
  - CloudFront + S3 for static hosting
- **Deployment** (`scripts/`)
  - `package-lambda.sh` - Build optimized Lambda package (8.9MB)
  - `deploy-ui.sh` - Deploy React app to CloudFront

### Planned Components (v1)
- **`data-ingestion/`** - Service to pull individual glucose data from Dexcom API
- **`data-processing/`** - Analytics engine for generating insights and recommendations
- **`email-service/`** - Scheduled email reports

## Deployment

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

**Quick start:**
```bash
# Deploy backend infrastructure
./scripts/package-lambda.sh
cd terraform && terraform apply -var-file=dev.tfvars

# Deploy frontend
./scripts/deploy-ui.sh
```