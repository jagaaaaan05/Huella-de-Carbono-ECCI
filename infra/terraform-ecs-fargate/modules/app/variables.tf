variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "database_url_secret_arn" {
  type = string
}

variable "image_tag" {
  description = "Etiqueta de la imagen en ECR que ejecuta el servicio"
  type        = string
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "cpu" {
  description = "Unidades de CPU de Fargate (256 = 0,25 vCPU)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memoria de la tarea en MiB"
  type        = number
  default     = 512
}

variable "gunicorn_workers" {
  type    = number
  default = 2
}

variable "min_tasks" {
  type    = number
  default = 1
}

variable "max_tasks" {
  type    = number
  default = 2
}

variable "domain_name" {
  description = "Dominio propio, p. ej. huella.ecci.edu.co. Vacío = usar el DNS del balanceador"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "Certificado ACM para HTTPS. Vacío = solo HTTP"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "container_insights" {
  type    = bool
  default = false
}

variable "force_delete_images" {
  description = "Permite destruir el repositorio ECR aunque tenga imágenes"
  type        = bool
  default     = false
}

variable "alarm_topic_arn" {
  description = "Tema SNS que recibe las alarmas. Vacío = sin notificación"
  type        = string
  default     = ""
}

variable "use_fargate_spot" {
  description = "Ejecutar las tareas en Fargate Spot (hasta 70 % más barato, AWS puede interrumpirlas)"
  type        = bool
  default     = false
}

variable "enable_execute_command" {
  description = "Permite abrir una consola en el contenedor con aws ecs execute-command"
  type        = bool
  default     = true
}

variable "alb_deletion_protection" {
  type    = bool
  default = false
}

variable "enable_waf" {
  type    = bool
  default = false
}

variable "waf_rate_limit" {
  description = "Peticiones máximas por IP cada 5 minutos"
  type        = number
  default     = 1000
}

variable "waf_write_rate_limit" {
  description = "Peticiones que no son GET permitidas por IP cada 5 minutos"
  type        = number
  default     = 100
}
