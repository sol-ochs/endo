# Endo

A proactive type 1 diabetes assistant.

The average diabetic sees their endocrinologist only 1-2 times a year. Endo aims to fill that gap with periodic "nudges," using your recent glucose data to generate timely insights and actionable recommendations between doctor visits.

## Architecture

### Current Components
- **Account Management**
  - **UI** (`ui/`)
    - React + TypeScript hosted on S3 + CloudFront
    - Cognito authentication
  - **User Management API** (`user-management-api/`)
    - FastAPI backend running on Lambda
    - JWT token security
    - Dexcom OAuth integration
- **Data Ingestion** (`data-ingestion/`)
  - **Lambda Layer** - Shared dependencies (`requests`)
  - **Coordinator Lambda** - Daily scheduled job to enqueue all users for data extraction
  - **SQS Queue** - Fan-out pattern for parallel processing with retry logic (3 retries → DLQ)
  - **Worker Lambda** - Processes individual users, fetches glucose data from Dexcom API
  - **S3 Storage** - Raw glucose data storage, partitioned on user_id and fetch_date
- **Infrastructure** (`terraform/`)
  - Terraform modules: S3, CloudFront, Lambda, Cognito, API Gateway, IAM, etc.
- **Deployment** (`scripts/`)
  - `package-lambda.sh` - Build optimized Lambda package (8.9MB)
  - `deploy-ui.sh` - Deploy React app to CloudFront

### Planned Components (v1)
- **`data-processing/`** - Analytics engine for generating insights and recommendations
- **`email-service/`** - Scheduled email reports

## Deployment

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).