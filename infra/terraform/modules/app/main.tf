# Django en AWS Lambda detrás de CloudFront, todo dentro de la capa Always Free:
#   CloudFront: 1 TB de salida, 10 millones de peticiones y 2 millones de funciones al mes.
#   Lambda: 1 millón de peticiones y 400 000 GB-segundo al mes.
#   CloudWatch: 5 GB de logs y 10 alarmas.
# Las URL de función de Lambda no tienen costo adicional.

locals {
  custom_domain = var.domain_name != "" && var.certificate_arn != ""
  mount_path    = "/mnt/data"
}

# ---------- Secretos ----------
# Van como variables de entorno de la función, cifradas con la llave administrada de AWS (gratis).
# Secrets Manager cobra 0,40 USD por secreto al mes y por eso no se usa.

resource "random_password" "django_secret_key" {
  length  = 64
  special = true
}

resource "random_password" "origin_verify" {
  length  = 48
  special = false
}

# ---------- Código inicial ----------
# Terraform crea la función con un marcador; GitHub Actions sube el código real.

data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/.build/placeholder.zip"

  source {
    filename = "ecci_carbon_footprint_dj/lambda_handler.py"
    content  = <<-PY
      def handler(event, context):
          return {"statusCode": 503, "body": "Despliegue pendiente: ejecute el workflow de GitHub Actions."}
    PY
  }
}

# ---------- IAM ----------

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.name}-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Logs en CloudWatch e interfaces de red en la VPC.
resource "aws_iam_role_policy_attachment" "vpc_access" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

data "aws_iam_policy_document" "efs" {
  statement {
    actions   = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "elasticfilesystem:AccessPointArn"
      values   = [var.efs_access_arn]
    }
  }
}

resource "aws_iam_role_policy" "efs" {
  name   = "efs"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.efs.json
}

# ---------- Función ----------

resource "aws_security_group" "lambda" {
  name        = "${var.name}-lambda"
  description = "Funcion Lambda: solo sale hacia EFS"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_egress_rule" "lambda_to_efs" {
  security_group_id = aws_security_group.lambda.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 2049
  to_port           = 2049
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = var.log_retention_days
}

# Lambda no puede montar EFS hasta que existan los puntos de montaje.
resource "terraform_data" "efs_ready" {
  input = var.efs_mount_targets
}

resource "aws_lambda_function" "this" {
  function_name    = var.name
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "ecci_carbon_footprint_dj.lambda_handler.handler"
  memory_size      = var.memory_mb
  timeout          = var.timeout_seconds
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  file_system_config {
    arn              = var.efs_access_arn
    local_mount_path = local.mount_path
  }

  environment {
    variables = {
      DJANGO_SETTINGS_MODULE = "ecci_carbon_footprint_dj.settings"
      DJANGO_DEBUG           = "False"
      DJANGO_SECRET_KEY      = random_password.django_secret_key.result
      DATABASE_URL           = "sqlite:///${local.mount_path}/db.sqlite3"
      # CloudFront solo acepta su dominio y los alias configurados, y la función rechaza
      # todo lo que no traiga el secreto de origen, así que aquí no hace falta filtrar el Host.
      DJANGO_ALLOWED_HOSTS                  = "*"
      DJANGO_SECURE_SSL_REDIRECT            = "False"
      DJANGO_SECURE_HSTS_SECONDS            = "31536000"
      DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS = "False"
      DJANGO_SECURE_HSTS_PRELOAD            = "False"
      ORIGIN_VERIFY_SECRET                  = random_password.origin_verify.result
    }
  }

  lifecycle {
    # El código lo publica GitHub Actions.
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [
    aws_iam_role_policy_attachment.vpc_access,
    aws_iam_role_policy.efs,
    aws_cloudwatch_log_group.this,
    terraform_data.efs_ready,
  ]
}

resource "aws_lambda_function_url" "this" {
  function_name      = aws_lambda_function.this.function_name
  authorization_type = "NONE"
}

# Una URL pública necesita los dos permisos. El segundo solo vale para llamadas que entran
# por la URL, así que nadie puede invocar la función directamente sin credenciales de IAM.
resource "aws_lambda_permission" "url" {
  statement_id           = "FunctionURLAllowPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.this.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "url_invoke" {
  statement_id             = "FunctionURLInvokeAllowPublicAccess"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.this.function_name
  principal                = "*"
  invoked_via_function_url = true
}

# ---------- CloudFront ----------

# Guarda el Host que pidió el visitante, porque CloudFront envía a Lambda el Host de la URL de la función.
resource "aws_cloudfront_function" "forward_host" {
  name    = "${var.name}-forward-host"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      request.headers['x-forwarded-host'] = { value: request.headers.host.value };
      return request;
    }
  JS
}

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_origin_request_policy" "all_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

resource "aws_cloudfront_distribution" "this" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = var.name
  aliases         = local.custom_domain ? [var.domain_name] : []
  # Solo Norteamérica y Europa: ninguna diferencia de costo dentro de la capa gratuita,
  # pero evita las regiones más caras si algún mes se supera.
  price_class = "PriceClass_100"

  origin {
    origin_id   = "lambda"
    domain_name = split("/", aws_lambda_function_url.this.function_url)[2]

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_read_timeout    = 30
    }

    custom_header {
      name  = "x-origin-verify"
      value = random_password.origin_verify.result
    }
  }

  default_cache_behavior {
    target_origin_id         = "lambda"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_except_host.id
    compress                 = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.forward_host.arn
    }
  }

  # Los archivos estáticos se guardan en la caché de CloudFront el tiempo que indique WhiteNoise.
  ordered_cache_behavior {
    path_pattern             = "/static/*"
    target_origin_id         = "lambda"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.optimized.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_except_host.id
    compress                 = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.forward_host.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = !local.custom_domain
    acm_certificate_arn            = local.custom_domain ? var.certificate_arn : null
    ssl_support_method             = local.custom_domain ? "sni-only" : null
    minimum_protocol_version       = local.custom_domain ? "TLSv1.2_2021" : null
  }
}

# ---------- Alarmas (gratis hasta 10) ----------

resource "aws_cloudwatch_metric_alarm" "errors" {
  alarm_name          = "${var.name}-errores"
  alarm_description   = "La función devolvió errores o se agotó su tiempo"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_topic_arn != "" ? [var.alarm_topic_arn] : []

  dimensions = {
    FunctionName = aws_lambda_function.this.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "throttles" {
  alarm_name          = "${var.name}-limitadas"
  alarm_description   = "Lambda rechazó peticiones por límite de concurrencia"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_topic_arn != "" ? [var.alarm_topic_arn] : []

  dimensions = {
    FunctionName = aws_lambda_function.this.function_name
  }
}
