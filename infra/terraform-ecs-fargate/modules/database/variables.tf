variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "allowed_security_group_ids" {
  description = "Grupos de seguridad que pueden conectarse al puerto 5432"
  type        = list(string)
}

variable "engine_version" {
  type    = string
  default = "16"
}

variable "instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "GB iniciales; crece automáticamente hasta 5 veces este valor"
  type        = number
  default     = 20
}

variable "db_name" {
  type    = string
  default = "huella"
}

variable "db_username" {
  type    = string
  default = "huella_app"
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = true
}

variable "alarm_topic_arn" {
  description = "Tema SNS que recibe las alarmas. Vacío = sin notificación"
  type        = string
  default     = ""
}
