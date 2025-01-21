provider "aws" {
  region = "eu-west-1"
}

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.84.0"
    }
  }
}
