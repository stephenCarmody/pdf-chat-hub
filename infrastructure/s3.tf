module "s3_vuejs" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.2.2"

  bucket = "chat-pdf-frontend"
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  website = {
    index_document = "index.html"
    error_document = "index.html"
  }

  cors_rule = [
    {
      allowed_methods = ["GET"]
      allowed_origins = ["*"]
      allowed_headers = ["*"]
      max_age_seconds = 3000
    }
  ]

  versioning = {
    enabled = true
  }
}

resource "aws_s3_bucket_policy" "allow_cloudfront" {
  bucket = module.s3_vuejs.s3_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipal"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${module.s3_vuejs.s3_bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.s3_distribution.arn
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket" "lambda_state" {
  bucket = "pdf-chat-lambda-state"
}

resource "aws_s3_bucket_lifecycle_configuration" "lambda_state" {
  bucket = aws_s3_bucket.lambda_state.id

  rule {
    id     = "cleanup_old_states"
    status = "Enabled"

    expiration {
      days = 1  # Delete states after 1 day
    }
  }
}

# Add S3 access policy for Lambda state management
resource "aws_iam_role_policy" "lambda_s3_state" {
  name = "lambda-s3-state-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*"  # Very permissive - allows all S3 actions
        ]
        Resource = [
          aws_s3_bucket.lambda_state.arn,
          "${aws_s3_bucket.lambda_state.arn}/*"
        ]
      }
    ]
  })
}
