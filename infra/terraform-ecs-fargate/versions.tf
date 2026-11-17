terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Los valores se pasan con: terraform init -backend-config=environments/<entorno>.backend.hcl
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "huella-carbono-ecci"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
