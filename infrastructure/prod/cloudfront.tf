resource "aws_cloudfront_origin_access_control" "s3_oac" {
  name                              = "chat-pdf-s3-oac"
  description                       = "Cloud Front OAC for S3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  enabled             = true
  default_root_object = "index.html"
  
  origin {
    domain_name              = module.s3_vuejs.s3_bucket_bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_oac.id
    origin_id               = "S3Origin"
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  // For SPA routing
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.cert.arn
    ssl_support_method = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  price_class = "PriceClass_100"  // Use only North America and Europe
  aliases = ["www.pdfchathub.com"]
}

# For ACM certificate
resource "aws_acm_certificate" "cert" {
  provider = aws.us-east-1  # Important: Certificate must be in us-east-1 for CloudFront
  domain_name = "www.pdfchathub.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Output the validation records so you can add them to Namecheap manually
output "certificate_validation_records" {
  value = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      value  = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
}

# Provider configuration
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}