output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.ebs_snapshot_cleanup.arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.ebs_snapshot_cleanup.function_name
}

output "cloudwatch_event_rule_arn" {
  description = "The ARN of the CloudWatch event rule"
  value       = aws_cloudwatch_event_rule.daily_ebs_cleanup.arn
}   