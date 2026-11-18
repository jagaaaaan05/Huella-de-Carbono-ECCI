locals {
  name            = "huella-${var.environment}"
  alarm_topic_arn = var.alarm_email != "" ? aws_sns_topic.alarms[0].arn : ""
}

module "network" {
  source     = "./modules/network"
  name       = local.name
  cidr_block = var.vpc_cidr
}

module "database" {
  source                     = "./modules/database"
  name                       = local.name
  vpc_id                     = module.network.vpc_id
  private_subnet_ids         = module.network.private_subnet_ids
  allowed_security_group_ids = [module.app.app_security_group_id]
  instance_class             = var.db_instance_class
  multi_az                   = var.db_multi_az
  backup_retention_days      = var.db_backup_retention_days
  deletion_protection        = var.db_deletion_protection
  alarm_topic_arn            = local.alarm_topic_arn
}

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
  source                  = "./modules/app"
  name                    = local.name
  vpc_id                  = module.network.vpc_id
  public_subnet_ids       = module.network.public_subnet_ids
  database_url_secret_arn = module.database.database_url_secret_arn
  image_tag               = var.image_tag != "" ? var.image_tag : var.environment
  cpu                     = var.app_cpu
  memory                  = var.app_memory
  min_tasks               = var.min_tasks
  max_tasks               = var.max_tasks
  domain_name             = var.domain_name
  certificate_arn         = var.certificate_arn
  force_delete_images     = var.environment != "prod"
  alarm_topic_arn         = local.alarm_topic_arn
  use_fargate_spot        = var.use_fargate_spot
  enable_waf              = var.enable_waf
  alb_deletion_protection = var.environment == "prod"
}

module "github_oidc" {
  count                = var.github_repository != "" ? 1 : 0
  source               = "./modules/github_oidc"
  name                 = local.name
  github_repository    = var.github_repository
  github_environment   = var.environment
  create_oidc_provider = var.create_github_oidc_provider
  ecr_repository_arn   = module.app.ecr_repository_arn
  ecs_service_arn      = module.app.service_arn
}
