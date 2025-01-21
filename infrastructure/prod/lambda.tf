resource "aws_security_group" "lambda" {
  name        = "pdf-chat-lambda"
  description = "Security group for Lambda function"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "pdf-chat-lambda-sg"
  }
}

resource "aws_lambda_function" "api" {
  function_name = "pdf-chat-api"
  package_type = "Image"
  image_uri    = "${var.lambda_image}"
  role         = aws_iam_role.lambda_role.arn
  architectures = ["arm64"]
  timeout      = 60
  memory_size  = 512
  source_code_hash = timestamp()
  publish = true

  vpc_config {
    subnet_ids         = aws_subnet.private_subnet[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  lifecycle {
    create_before_destroy = true
  }

  environment {
    variables = {
      CLOUDFRONT_DOMAIN = aws_cloudfront_distribution.s3_distribution.domain_name,
      OPENAI_SECRET_NAME = aws_secretsmanager_secret.openai_api_key.name,
      SESSION_STATE_BUCKET = aws_s3_bucket.lambda_state.bucket,
      DB_HOST = aws_rds_cluster.aurora.endpoint,
      DB_NAME = aws_rds_cluster.aurora.database_name,
      DB_USER = aws_rds_cluster.aurora.master_username,
      DB_PASSWORD = "password"  # Simple password for development
    }
  }

  image_config {
    command = ["lambda_handler.handler"]
  }
}

# Output the Lambda security group ID for use in RDS
output "lambda_security_group_id" {
  value = aws_security_group.lambda.id
}

resource "aws_apigatewayv2_api" "api" {
  name          = "pdf-chat-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = [
      "https://dt6q0e1osg5xr.cloudfront.net",
      "https://www.pdfchathub.com",
      "http://localhost:5173" 
    ]
    allow_methods = ["POST", "GET", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "api" {
  api_id = aws_apigatewayv2_api.api.id
  name   = "prod"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "api" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds = 30000
}

resource "aws_apigatewayv2_route" "api" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

# OPTIONS route - required for CORS
resource "aws_apigatewayv2_route" "options" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "OPTIONS /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
} 

# Add this new route for root path
resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

# Allow API Gateway to invoke the Lambda function
resource "aws_lambda_permission" "api_gateway_root" {
  statement_id  = "AllowAPIGatewayInvokeRoot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
