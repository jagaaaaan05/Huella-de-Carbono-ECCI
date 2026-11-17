# Firewall de aplicaciones (WAF) delante del balanceador.
# Limita peticiones por IP y bloquea ataques comunes. Mientras la API no tenga
# autenticación, el límite de escrituras frena el abuso de POST/PATCH/DELETE anónimos.

resource "aws_wafv2_web_acl" "this" {
  count = var.enable_waf ? 1 : 0
  name  = "${var.name}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "limite-escrituras-por-ip"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_write_rate_limit
        aggregate_key_type = "IP"

        # Cuenta solo las peticiones que no son GET.
        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string         = "GET"
                positional_constraint = "EXACTLY"
                field_to_match {
                  method {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name}-write-rate"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "limite-general-por-ip"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name}-rate"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "aws-reglas-comunes"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"

        # El límite de 8 KB del cuerpo bloquearía cargas legítimas de inventario; solo se cuenta.
        rule_action_override {
          name = "SizeRestrictions_BODY"
          action_to_use {
            count {}
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name}-common"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "aws-entradas-maliciosas"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name}-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.name}-waf"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "this" {
  count        = var.enable_waf ? 1 : 0
  resource_arn = aws_lb.this.arn
  web_acl_arn  = aws_wafv2_web_acl.this[0].arn
}
