# Crea el bucket S3 del estado remoto de Terraform y un aviso de presupuesto.
# Se aplica una sola vez por cuenta, con estado local.
# El bloqueo usa el archivo .tflock de S3 (Terraform >= 1.10), así que no hace falta DynamoDB.

terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "state_bucket_name" {
  description = "Nombre único global del bucket de estado, p. ej. ecci-huella-tfstate-<cuenta>"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "Nombre de bucket inválido: 3-63 caracteres, minúsculas, números, '.' o '-', y no puede terminar en '-'."
  }
}

variable "budget_email" {
  description = "Correo que recibe el aviso de presupuesto. Vacío = no crear presupuesto"
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Gasto mensual que dispara el aviso. Con 1 USD avisa ante cualquier cobro real"
  type        = number
  default     = 1
}

resource "aws_s3_bucket" "state" {
  bucket = var.state_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Las versiones viejas del estado se borran a los 30 días para no acumular almacenamiento.
resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    id     = "versiones-antiguas"
    status = "Enabled"
    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Los dos primeros presupuestos de AWS Budgets son gratuitos.
resource "aws_budgets_budget" "monthly" {
  count        = var.budget_email != "" ? 1 : 0
  name         = "huella-mensual"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_email]
  }
}

output "state_bucket" {
  value = aws_s3_bucket.state.bucket
}
