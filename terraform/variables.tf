variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "cognito_callback_urls" {
  description = "List of callback URLs for Cognito"
  type        = list(string)
}

variable "cognito_logout_urls" {
  description = "List of logout URLs for Cognito"
  type        = list(string)
}

variable "dexcom_client_id" {
  description = "Dexcom OAuth client ID"
  type        = string
  sensitive   = true
}

variable "dexcom_client_secret" {
  description = "Dexcom OAuth client secret"
  type        = string
  sensitive   = true
}

variable "dexcom_redirect_uri" {
  description = "Dexcom OAuth redirect URI"
  type        = string
}

variable "frontend_base_url" {
  description = "Frontend base URL for OAuth redirects"
  type        = string
  default     = "http://localhost:3000"
}

variable "dexcom_api_base_url" {
  description = "Dexcom API base URL (sandbox or production)"
  type        = string
  default     = "https://sandbox-api.dexcom.com"
}