# Endo

A proactive type 1 diabetes assistant.

The average diabetic sees their endocrinologist only 1-2 times a year. Endo aims to fill that void with periodic "nudges," using your recent glucose data to generate timely insights and actionable recommendations between doctor visits.

## Architecture

### Current Components
- **`ui/`** - React 18 + TypeScript frontend with React Router, Axios, and Lucide icons
- **`user-management-api/`** - FastAPI backend with AWS Cognito auth and DynamoDB storage (deployed on AWS Lambda for cost efficiency)
- **`terraform/`** - AWS infrastructure (Cognito, DynamoDB) with dev/prod environments

### Planned Components (v1)
- **`data-ingestion/`** - Service to pull individual glucose data from Dexcom API
- **`data-processing/`** - Analytics engine for generating insights and recommendations
- **`email-service/`** - Scheduled email reports

## Deployment

For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).