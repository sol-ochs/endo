# Endo

A type 1 diabetes assistant providing daily support and management tools.

The average type 1 diabetic sees their endocrinologist only 1-2 times a year. Endo aims to fill this gap by providing continuous glucose monitoring insights, trend analysis, and personalized recommendations between doctor visits.

## Architecture

### Current Components
- **`ui/`** - React 18 + TypeScript frontend with React Router, Axios, and Lucide icons
- **`user-management-api/`** - FastAPI backend with AWS Cognito auth and DynamoDB storage (deployed on AWS Lambda for cost efficiency)
- **`terraform/`** - AWS infrastructure (Cognito, DynamoDB) with dev/prod environments

### Planned Components (v1)
- **`data-ingestion/`** - Service to pull individual glucose data from Dexcom API
- **`data-processing/`** - Analytics engine for generating insights and recommendations
- **`email-service/`** - Scheduled email reports

## Quick Start

For detailed step-by-step instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).