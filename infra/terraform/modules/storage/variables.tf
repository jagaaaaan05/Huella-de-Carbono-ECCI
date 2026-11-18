variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "allowed_security_group_ids" {
  description = "Grupos de seguridad que pueden montar el sistema de archivos"
  type        = list(string)
}

variable "backups" {
  type    = bool
  default = false
}
