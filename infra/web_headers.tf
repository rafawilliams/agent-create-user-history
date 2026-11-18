# Politica de cabeceras de la pantalla (NFR5.9): la politica de contenido exacta de NFR5.4 de u5 y
# las demas cabeceras de seguridad. Depende del identificador de la API REST y del prefijo del
# dominio de Cognito, pero no de la etapa ni del despliegue de la pasarela (sin ciclos).

locals {
  api_origin     = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${var.region}.amazonaws.com"
  cognito_origin = "https://${var.cognito_domain_prefix}.auth.${var.region}.amazoncognito.com"

  # `unsafe-inline` solo en estilos: riesgo aceptado porque MUI con emotion inyecta etiquetas de
  # estilo en tiempo de ejecucion; los scripts siguen sin permitir codigo en linea.
  content_security_policy = join("; ", [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "connect-src 'self' ${local.api_origin} ${local.cognito_origin} https://cognito-idp.${var.region}.amazonaws.com",
    "img-src 'self' data:",
    "font-src 'self' data:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ])
}

resource "aws_cloudfront_response_headers_policy" "web" {
  name    = "${var.name_prefix}-web-security"
  comment = "Cabeceras de seguridad de la pantalla (NFR5.9)"

  security_headers_config {
    content_security_policy {
      content_security_policy = local.content_security_policy
      override                = true
    }

    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    referrer_policy {
      referrer_policy = "no-referrer"
      override        = true
    }
  }
}
