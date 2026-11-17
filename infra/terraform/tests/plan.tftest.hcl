# Pruebas sin credenciales: terraform test (proveedores simulados, requiere Terraform >= 1.10).

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = { names = ["us-east-2a", "us-east-2b", "us-east-2c"] }
  }
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
  mock_data "aws_caller_identity" {
    defaults = { account_id = "123456789012" }
  }
  mock_data "aws_cloudfront_cache_policy" {
    defaults = { id = "658327ea-f89d-4fab-a63d-7e88639e58f6" }
  }
  mock_data "aws_cloudfront_origin_request_policy" {
    defaults = { id = "b689b0a8-53d0-40ab-baf2-68738e2966ac" }
  }
  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::123456789012:role/x" }
  }
  mock_resource "aws_efs_access_point" {
    defaults = { arn = "arn:aws:elasticfilesystem:us-east-2:123456789012:access-point/fsap-1" }
  }
  mock_resource "aws_lambda_function" {
    defaults = { arn = "arn:aws:lambda:us-east-2:123456789012:function:huella" }
  }
  mock_resource "aws_lambda_function_url" {
    defaults = { function_url = "https://abc123.lambda-url.us-east-2.on.aws/" }
  }
  mock_resource "aws_cloudfront_function" {
    defaults = { arn = "arn:aws:cloudfront::123456789012:function/x" }
  }
  mock_resource "aws_cloudfront_distribution" {
    defaults = { domain_name = "d111111abcdef8.cloudfront.net" }
  }
  mock_resource "aws_sns_topic" {
    defaults = { arn = "arn:aws:sns:us-east-2:123456789012:x" }
  }
}
mock_provider "random" {}
mock_provider "archive" {
  mock_data "archive_file" {
    defaults = { output_path = "placeholder.zip", output_base64sha256 = "x" }
  }
}

run "staging_cloudfront" {
  command = apply
  variables {
    environment = "staging"
  }
  assert {
    condition     = output.app_url == "https://d111111abcdef8.cloudfront.net"
    error_message = "staging debe servir por HTTPS en el dominio de CloudFront"
  }
  assert {
    condition     = module.app.function_name == "huella-staging"
    error_message = "nombre de la función"
  }
  assert {
    condition     = output.github_deploy_role_arn == null
    error_message = "sin repo no hay rol"
  }
}

run "prod_dominio_propio" {
  command = apply
  variables {
    environment       = "prod"
    domain_name       = "huella.ecci.edu.co"
    certificate_arn   = "arn:aws:acm:us-east-1:123456789012:certificate/abc"
    github_repository = "jagaaaaan05/Huella-de-Carbono-ECCI"
    alarm_email       = "a@b.co"
    efs_backups       = true
  }
  assert {
    condition     = output.app_url == "https://huella.ecci.edu.co"
    error_message = "prod con dominio debe usar ese dominio"
  }
  assert {
    condition     = output.github_deploy_role_arn != null
    error_message = "debe crear el rol de despliegue"
  }
}

run "timeout_mayor_a_cloudfront" {
  command = plan
  variables {
    environment            = "staging"
    lambda_timeout_seconds = 60
  }
  expect_failures = [var.lambda_timeout_seconds]
}
