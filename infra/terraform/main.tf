locals {
  name            = "huella-${var.environment}"
  alarm_topic_arn = var.alarm_email != "" ? aws_sns_topic.alarms[0].arn : ""
}

module "network" {
  source     = "./modules/network"
  name       = local.name
  cidr_block = var.vpc_cidr
}

module "storage" {
  source                     = "./modules/storage"
  name                       = local.name
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.private_subnet_ids
  allowed_security_group_ids = [module.app.lambda_security_group_id]
  backups                    = var.efs_backups
}

# SNS es gratuito hasta 1000 correos al mes.
resource "aws_sns_topic" "alarms" {
  count = var.alarm_email != "" ? 1 : 0
  name  = "${local.name}-alarms"
}

resource "aws_sns_topic_subscription" "alarms_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

module "app" {
  source            = "./modules/app"
  name              = local.name
  vpc_id            = module.network.vpc_id
  subnet_ids        = module.network.private_subnet_ids
  efs_access_arn    = module.storage.access_point_arn
  efs_mount_targets = module.storage.mount_target_ids
  memory_mb         = var.lambda_memory_mb
  timeout_seconds   = var.lambda_timeout_seconds
  domain_name       = var.domain_name
  certificate_arn   = var.certificate_arn
  alarm_topic_arn   = local.alarm_topic_arn
}

module "github_oidc" {
  count                = var.github_repository != "" ? 1 : 0
  source               = "./modules/github_oidc"
  name                 = local.name
  github_repository    = var.github_repository
  github_environment   = var.environment
  create_oidc_provider = var.create_github_oidc_provider
  lambda_function_arn  = module.app.function_arn
}
