data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "ebs_snapshot_cleanup" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "ebs-snapshot-cleanup"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.9"

  environment {
    variables = {
      AWS_REGIONS     = join(",", var.aws_regions)
      RETENTION_DAYS  = var.retention_days
      DRY_RUN         = var.dry_run
      SENDER_EMAIL    = var.sender_email
      RECIPIENT_EMAIL = var.recipient_email
      SES_REGION      = var.ses_region
    }
  }

  timeout     = 300
  memory_size = 128
}