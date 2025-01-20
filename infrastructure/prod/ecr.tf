resource "aws_ecr_repository" "lambda_ecr" {
  name = "pdf-chat-api"
}

resource "aws_ecr_lifecycle_policy" "lambda_policy" {
  repository = aws_ecr_repository.lambda_ecr.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 3 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 3
      }
      action = {
        type = "expire"
      }
    }]
  })
}
