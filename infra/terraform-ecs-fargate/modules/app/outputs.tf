output "url" {
  value = "${local.scheme}://${local.public_host}"
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.this.repository_url
}

output "ecr_repository_arn" {
  value = aws_ecr_repository.this.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_name" {
  value = aws_ecs_service.this.name
}

output "service_arn" {
  value = aws_ecs_service.this.id
}

output "app_security_group_id" {
  value = aws_security_group.app.id
}

output "task_definition_family" {
  value = aws_ecs_task_definition.this.family
}

output "task_role_arns" {
  value = [aws_iam_role.execution.arn, aws_iam_role.task.arn]
}

output "waf_web_acl_arn" {
  value = var.enable_waf ? aws_wafv2_web_acl.this[0].arn : null
}

output "capacity_provider" {
  value = local.capacity_provider
}
