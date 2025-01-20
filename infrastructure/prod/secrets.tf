# Create the secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "pdf-chat/openai-api-key"
  description = "OpenAI API Key for PDF Chat"
}

# IAM policy for Lambda to access the secret
resource "aws_iam_role_policy" "lambda_secrets" {
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.openai_api_key.arn
      }
    ]
  })
}
