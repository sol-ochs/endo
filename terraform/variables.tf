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
  description = "Dexcom API client ID"
  type        = string
  sensitive   = true
}

variable "dexcom_client_secret" {
  description = "Dexcom API client secret"
  type        = string
  sensitive   = true
}

variable "dexcom_redirect_uri" {
  description = "Dexcom OAuth redirect URI"
  type        = string
}