variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "efs_access_arn" {
  description = "ARN del punto de acceso de EFS donde vive db.sqlite3"
  type        = string
}

variable "efs_mount_targets" {
  description = "Puntos de montaje que deben existir antes de crear la función"
  type        = list(string)
}

variable "memory_mb" {
  type    = number
  default = 1024
}

variable "timeout_seconds" {
  description = "Máximo 30: es el tiempo que CloudFront espera la respuesta"
  type        = number
  default     = 30

  validation {
    condition     = var.timeout_seconds <= 30
    error_message = "CloudFront corta a los 30 segundos; un timeout mayor no sirve."
  }
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "certificate_arn" {
  type    = string
  default = ""
}

variable "alarm_topic_arn" {
  type    = string
  default = ""
}
