variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "environment" {
  description = "staging o prod"
  type        = string

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment debe ser staging o prod."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "lambda_memory_mb" {
  description = "Memoria de la función. La capa gratuita cubre 400 000 GB-segundo al mes"
  type        = number
  default     = 1024
}

variable "lambda_timeout_seconds" {
  description = "Máximo 30: es el tiempo que CloudFront espera la respuesta"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout_seconds <= 30
    error_message = "CloudFront corta a los 30 segundos; un timeout mayor no sirve."
  }
}

variable "efs_backups" {
  description = "Copias diarias de la base SQLite con AWS Backup (centavos al mes)"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Dominio propio, p. ej. huella.ecci.edu.co. Vacío = usar el dominio de CloudFront"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "Certificado de ACM en us-east-1 para el dominio propio (ACM es gratuito)"
  type        = string
  default     = ""
}

variable "alarm_email" {
  description = "Correo que recibe las alarmas. Vacío = sin notificación"
  type        = string
  default     = ""
}

variable "github_repository" {
  description = "propietario/repositorio para el despliegue con GitHub Actions. Vacío = no crear el rol"
  type        = string
  default     = ""
}

variable "create_github_oidc_provider" {
  type    = bool
  default = true
}
