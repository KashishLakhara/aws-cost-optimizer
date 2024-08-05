resource "aws_cloudwatch_event_rule" "daily_ebs_cleanup" {
  name                = "daily-ebs-snapshot-cleanup"
  description         = "Triggers EBS snapshot cleanup Lambda function daily"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.daily_ebs_cleanup.name
  target_id = "TriggerEBSSnapshotCleanup"
  arn       = aws_lambda_function.ebs_snapshot_cleanup.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ebs_snapshot_cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ebs_cleanup.arn
}