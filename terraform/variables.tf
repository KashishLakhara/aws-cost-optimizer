variable "primary_region" {
  description = "The primary AWS region for deploying resources"
  type        = string
  default     = "us-east-1"
}

variable "ses_region" {
  description = "The AWS region where SES is set up"
  type        = string
  default     = "us-east-1"
}

variable "aws_regions" {
  description = "List of AWS regions to clean up EBS snapshots"
  type        = list(string)
  default     = ["us-east-1", "us-west-2"]
}

variable "retention_days" {
  description = "Number of days to retain snapshots"
  type        = number
  default     = 30
}

variable "dry_run" {
  description = "Whether to perform a dry run without actually deleting snapshots"
  type        = bool
  default     = false
}

variable "sender_email" {
  description = "Email address to send reports from"
  type        = string
}

variable "recipient_email" {
  description = "Email address to send reports to"
  type        = string
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression for running the Lambda function"
  type        = string
  default     = "rate(1 day)"
}