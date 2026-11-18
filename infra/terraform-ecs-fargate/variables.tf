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

variable "image_tag" {
  description = "Etiqueta de la imagen que ejecuta ECS; el pipeline publica una con el nombre del entorno"
  type        = string
  default     = ""
}

variable "app_cpu" {
  type    = number
  default = 256
}

variable "app_memory" {
  type    = number
  default = 512
}

variable "min_tasks" {
  type    = number
  default = 1
}

variable "max_tasks" {
  type    = number
  default = 2
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_multi_az" {
  type    = bool
  default = false
}

variable "db_backup_retention_days" {
  type    = number
  default = 7
}

variable "db_deletion_protection" {
  type    = bool
  default = true
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "certificate_arn" {
  type    = string
  default = ""
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

variable "use_fargate_spot" {
  description = "Ejecutar las tareas en Fargate Spot (recomendado solo en staging)"
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "Poner un WAF con límite de peticiones por IP delante del balanceador (~10 USD/mes)"
  type        = bool
  default     = false
}
