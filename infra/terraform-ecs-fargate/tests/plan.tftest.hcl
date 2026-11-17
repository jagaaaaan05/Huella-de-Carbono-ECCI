# Pruebas sin credenciales: terraform test (proveedores simulados, requiere Terraform >= 1.7).

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = { names = ["us-east-2a", "us-east-2b", "us-east-2c"] }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_data "aws_region" {
    defaults = { region = "us-east-2" }
  }
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_resource "aws_lb" {
    defaults = { dns_name = "huella-alb-123.us-east-2.elb.amazonaws.com", arn = "arn:aws:elasticloadbalancing:us-east-2:123456789012:loadbalancer/app/x/1" }
  }
  mock_resource "aws_secretsmanager_secret" {
    defaults = { arn = "arn:aws:secretsmanager:us-east-2:123456789012:secret:x" }
  }
  mock_resource "aws_ecr_repository" {
    defaults = { repository_url = "123456789012.dkr.ecr.us-east-2.amazonaws.com/huella", arn = "arn:aws:ecr:us-east-2:123456789012:repository/huella" }
  }
  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::123456789012:role/x" }
  }
  mock_resource "aws_lb_target_group" {
    defaults = { arn = "arn:aws:elasticloadbalancing:us-east-2:123456789012:targetgroup/x/1" }
  }
  mock_resource "aws_ecs_task_definition" {
    defaults = { arn = "arn:aws:ecs:us-east-2:123456789012:task-definition/x:1" }
  }
  mock_resource "aws_ecs_service" {
    defaults = { id = "arn:aws:ecs:us-east-2:123456789012:service/x/x" }
  }
  mock_resource "aws_wafv2_web_acl" {
    defaults = { arn = "arn:aws:wafv2:us-east-2:123456789012:regional/webacl/x/1" }
  }
  mock_resource "aws_sns_topic" {
    defaults = { arn = "arn:aws:sns:us-east-2:123456789012:x" }
  }
}
mock_provider "random" {}

run "staging_http" {
  command = apply
  variables {
    environment            = "staging"
    db_deletion_protection = false
    use_fargate_spot       = true
  }
  assert {
    condition     = module.app.capacity_provider == "FARGATE_SPOT"
    error_message = "staging debe correr en Fargate Spot"
  }
  assert {
    condition     = output.waf_web_acl_arn == null
    error_message = "staging no lleva WAF"
  }
  assert {
    condition     = output.app_url == "http://huella-alb-123.us-east-2.elb.amazonaws.com"
    error_message = "staging debe servir por HTTP en el DNS del ALB"
  }
  assert {
    condition     = length(module.app.task_role_arns) == 2
    error_message = "roles"
  }
  assert {
    condition     = output.github_deploy_role_arn == null
    error_message = "sin repo no hay rol"
  }
}

run "prod_https" {
  command = apply
  variables {
    environment       = "prod"
    domain_name       = "huella.ecci.edu.co"
    certificate_arn   = "arn:aws:acm:us-east-2:123456789012:certificate/abc"
    github_repository = "jagaaaaan05/Huella-de-Carbono-ECCI"
    alarm_email       = "a@b.co"
    enable_waf        = true
  }
  assert {
    condition     = module.app.capacity_provider == "FARGATE"
    error_message = "prod debe correr en Fargate normal"
  }
  assert {
    condition     = output.waf_web_acl_arn != null
    error_message = "prod debe tener WAF"
  }
  assert {
    condition     = output.app_url == "https://huella.ecci.edu.co"
    error_message = "prod con dominio debe usar https"
  }
  assert {
    condition     = output.github_deploy_role_arn != null
    error_message = "debe crear el rol de despliegue"
  }
}
