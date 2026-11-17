variable "name" {
  type = string
}

variable "github_repository" {
  description = "Repositorio en formato propietario/nombre"
  type        = string
}

variable "github_environment" {
  description = "Entorno de GitHub Actions autorizado a desplegar"
  type        = string
}

variable "create_oidc_provider" {
  description = "false si la cuenta ya tiene el proveedor OIDC de GitHub"
  type        = bool
  default     = true
}

variable "lambda_function_arn" {
  type = string
}
