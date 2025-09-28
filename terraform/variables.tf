variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev or prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "endo"
}

variable "cognito_callback_urls" {
  description = "List of callback URLs for Cognito"
  type        = list(string)
  default     = [
    "http://localhost:3000/dexcom/callback",
    "http://localhost:3000/auth/callback"
  ]
}

variable "cognito_logout_urls" {
  description = "List of logout URLs for Cognito"
  type        = list(string)
  default     = [
    "http://localhost:3000/login"
  ]
}