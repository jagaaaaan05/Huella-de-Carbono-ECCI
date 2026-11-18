environment              = "prod"
vpc_cidr                 = "10.30.0.0/16"
min_tasks                = 1
max_tasks                = 3
db_instance_class        = "db.t4g.small"
db_multi_az              = false
db_backup_retention_days = 7
db_deletion_protection   = true
use_fargate_spot         = false
enable_waf               = true

# Para HTTPS con dominio propio: crear el certificado en ACM y poner su ARN aquí.
# domain_name     = "huella.ecci.edu.co"
# certificate_arn = "arn:aws:acm:us-east-2:123456789012:certificate/..."

# github_repository           = "jagaaaaan05/Huella-de-Carbono-ECCI"
# create_github_oidc_provider = false   # ya lo creó staging en la misma cuenta
# alarm_email                 = "correo@ejemplo.com"
