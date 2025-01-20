output "cloudfront_domain" {
  description = "The domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.s3_distribution.domain_name
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket hosting the static website"
  value       = module.s3_vuejs.s3_bucket_id
}

output "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = module.s3_vuejs.s3_bucket_arn
}

output "api_gateway_url" {
  description = "The URL of the API Gateway endpoint"
  value       = aws_apigatewayv2_api.api.api_endpoint
}
