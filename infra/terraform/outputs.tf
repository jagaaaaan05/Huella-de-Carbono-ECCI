output "app_url" {
  description = "URL pública de la aplicación"
  value       = module.app.url
}

output "cloudfront_domain" {
  description = "Destino del CNAME si se usa un dominio propio"
  value       = module.app.cloudfront_domain
}

output "lambda_function_name" {
  value = module.app.function_name
}

output "github_deploy_role_arn" {
  value = length(module.github_oidc) > 0 ? module.github_oidc[0].role_arn : null
}
