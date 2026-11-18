environment      = "prod"
vpc_cidr         = "10.30.0.0/16"
lambda_memory_mb = 1024
efs_backups      = true # copias diarias de la base, centavos al mes

# Dominio propio: crear el certificado en ACM (us-east-1, gratuito), poner su ARN aquí
# y crear en el DNS de la universidad un CNAME hacia el output cloudfront_domain.
# domain_name     = "huella.ecci.edu.co"
# certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."

# github_repository           = "jagaaaaan05/Huella-de-Carbono-ECCI"
# create_github_oidc_provider = false   # ya lo creó staging en la misma cuenta
# alarm_email                 = "correo@ejemplo.com"
