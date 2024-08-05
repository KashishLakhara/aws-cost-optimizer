resource "aws_iam_role" "lambda_exec" {
  name = "ebs-snapshot-cleanup-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_exec.name
}

resource "aws_iam_policy" "ec2_snapshot_access" {
  name        = "ebs-snapshot-cleanup-ec2-policy"
  path        = "/"
  description = "IAM policy for EBS snapshot cleanup Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeSnapshots",
          "ec2:DescribeVolumes",
          "ec2:DeleteSnapshot"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_snapshot_access" {
  policy_arn = aws_iam_policy.ec2_snapshot_access.arn
  role       = aws_iam_role.lambda_exec.name
}

resource "aws_iam_policy" "ses_send_email" {
  name        = "ebs-snapshot-cleanup-ses-policy"
  path        = "/"
  description = "IAM policy for sending emails via SES"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ses_send_email" {
  policy_arn = aws_iam_policy.ses_send_email.arn
  role       = aws_iam_role.lambda_exec.name
}