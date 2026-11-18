output "app_url" {
  description = "URL pública de la aplicación"
  value       = module.app.url
}

output "ecr_repository_url" {
  value = module.app.ecr_repository_url
}

output "ecs_cluster" {
  value = module.app.cluster_name
}

output "ecs_service" {
  value = module.app.service_name
}

output "ecs_task_definition_family" {
  value = module.app.task_definition_family
}

output "database_endpoint" {
  value = module.database.endpoint
}

output "github_deploy_role_arn" {
  value = length(module.github_oidc) > 0 ? module.github_oidc[0].role_arn : null
}

output "waf_web_acl_arn" {
  value = module.app.waf_web_acl_arn
}
