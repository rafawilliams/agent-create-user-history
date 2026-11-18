data "aws_caller_identity" "current" {}

locals {
  base_model_id = replace(var.bedrock_model_id, "/^(us|global)\\./", "")
  model_arns = length(var.bedrock_model_arns) > 0 ? var.bedrock_model_arns : [
    "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:inference-profile/${var.bedrock_model_id}",
    # El perfil de inferencia enruta entre regiones, por eso la region del modelo base es comodin.
    "arn:aws:bedrock:*::foundation-model/${local.base_model_id}",
  ]
  function_name = "${var.name_prefix}-story-service"
  web_origin    = "https://${aws_cloudfront_distribution.web.domain_name}"
  # Limite de permisos que crea infra/bootstrap (mismo nombre): todo rol que se cree lo lleva (NFR5.4).
  permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/pipeline-${var.name_prefix}-boundary"
}

# ---------------------------------------------------------------------------
# Funcion Lambda (servicio de generacion, Python). Sin estado, sin almacen de datos (NFR4.1).
# ---------------------------------------------------------------------------

# El zip sale de infra/build/package, que construye `python infra/scripts/build_lambda_package.py`
# (codigo de backend/story_service como paquete de nivel superior mas las dependencias de
# backend/requirements.txt instaladas para Lambda python3.12 y Linux x86_64). Hay que ejecutar el
# script antes de plan y apply: sin PyJWT[crypto] la funcion falla al importar `jwt`.
data "archive_file" "story_service" {
  type        = "zip"
  source_dir  = "${path.module}/build/package"
  output_path = "${path.module}/build/story_service.zip"
  excludes    = ["**/__pycache__"]
}

resource "aws_cloudwatch_log_group" "story" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "story" {
  function_name                  = local.function_name
  role                           = aws_iam_role.story.arn
  runtime                        = "python3.12"
  handler                        = "story_service.handler.lambda_handler"
  filename                       = data.archive_file.story_service.output_path
  source_code_hash               = data.archive_file.story_service.output_base64sha256
  memory_size                    = 512
  timeout                        = 57
  publish                        = true
  reserved_concurrent_executions = var.reserved_concurrency

  environment {
    variables = {
      # Desplegado: el servicio verifica el token de Cognito (u4). ALLOW_SIMULATED_SESSION NO se
      # define a proposito (BR1.5, NFR5.2): sin verificador real, el servicio falla cerrado.
      APP_ENV               = "prod"
      BEDROCK_MODEL_ID      = var.bedrock_model_id
      BEDROCK_REGION        = var.region
      CORS_ALLOWED_ORIGIN   = local.web_origin
      COGNITO_REGION        = var.region
      COGNITO_USER_POOL_ID  = aws_cognito_user_pool.main.id
      COGNITO_APP_CLIENT_ID = aws_cognito_user_pool_client.web.id
      ALLOWED_EMAILS        = var.allowed_emails
    }
  }

  depends_on = [aws_cloudwatch_log_group.story, aws_iam_role_policy.story]
}

# Alias estable; el retroceso es volver a aplicar con live_version = version anterior.
resource "aws_lambda_alias" "live" {
  name             = "live"
  function_name    = aws_lambda_function.story.function_name
  function_version = var.live_version != "" ? var.live_version : aws_lambda_function.story.version
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.story.function_name
  qualifier     = aws_lambda_alias.live.name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

# Metricas a partir de los registros estructurados (observability-design.md).
resource "aws_cloudwatch_log_metric_filter" "requests_total" {
  name           = "requests_total"
  log_group_name = aws_cloudwatch_log_group.story.name
  pattern        = "{ $.metric = \"requests_total\" }"

  metric_transformation {
    name      = "requests_total"
    namespace = "BusinessAnalystAgent"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "errors_total" {
  name           = "errors_total"
  log_group_name = aws_cloudwatch_log_group.story.name
  pattern        = "{ $.metric = \"errors_total\" }"

  metric_transformation {
    name      = "errors_total"
    namespace = "BusinessAnalystAgent"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "generation_duration_ms" {
  name           = "generation_duration_ms"
  log_group_name = aws_cloudwatch_log_group.story.name
  pattern        = "{ $.metric = \"generation_duration_ms\" }"

  metric_transformation {
    name      = "generation_duration_ms"
    namespace = "BusinessAnalystAgent"
    value     = "$.value"
  }
}

# ---------------------------------------------------------------------------
# Pasarela REST: limite de uso (429 RATE_LIMITED) e integracion de 58 s.
# ---------------------------------------------------------------------------

resource "aws_api_gateway_rest_api" "api" {
  name = "${var.name_prefix}-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "v1"
}

resource "aws_api_gateway_resource" "stories" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "stories"
}

# La credencial de sesion la verifica el servicio (C3), no la pasarela.
resource "aws_api_gateway_method" "post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.stories.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.stories.id
  http_method             = aws_api_gateway_method.post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.live.invoke_arn
  timeout_milliseconds    = var.integration_timeout_ms
}

# CORS: la solicitud previa (OPTIONS) la responde la pasarela solo para el origen de la pantalla,
# en /v1/stories y en /v1/session (NFR5.9).
locals {
  preflight_resources = {
    stories = aws_api_gateway_resource.stories.id
    session = aws_api_gateway_resource.session.id
  }
}

resource "aws_api_gateway_method" "options" {
  for_each = local.preflight_resources

  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = each.value
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  for_each = local.preflight_resources

  rest_api_id       = aws_api_gateway_rest_api.api.id
  resource_id       = each.value
  http_method       = aws_api_gateway_method.options[each.key].http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 204}" }
}

resource "aws_api_gateway_method_response" "options" {
  for_each = local.preflight_resources

  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = each.value
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "204"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each = local.preflight_resources

  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = each.value
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.web_origin}'"
    "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,DELETE,OPTIONS'"
  }

  depends_on = [aws_api_gateway_integration.options]
}

# 429 personalizado con la forma del error de C1; sin requestId (ocurre antes del servicio).
resource "aws_api_gateway_gateway_response" "throttled" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "THROTTLED"
  status_code   = "429"

  response_templates = {
    "application/json" = jsonencode({
      code      = "RATE_LIMITED"
      message   = "Demasiadas solicitudes. Espera un momento e inténtalo de nuevo."
      retryable = true
    })
  }

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'${local.web_origin}'"
  }
}

locals {
  api_redeployment_hash = sha1(jsonencode({
    resources = [
      aws_api_gateway_resource.v1.path_part,
      aws_api_gateway_resource.stories.path_part,
      aws_api_gateway_resource.session.path_part,
    ]
    methods = {
      post    = [aws_api_gateway_method.post.http_method, aws_api_gateway_method.post.authorization]
      session = { for k, m in aws_api_gateway_method.session : k => [m.http_method, m.authorization] }
      options = { for k, m in aws_api_gateway_method.options : k => [m.http_method, m.authorization] }
    }
    integrations = {
      post = [
        aws_api_gateway_integration.post.type,
        aws_api_gateway_integration.post.uri,
        aws_api_gateway_integration.post.integration_http_method,
        aws_api_gateway_integration.post.timeout_milliseconds,
      ]
      session = { for k, i in aws_api_gateway_integration.session : k => [i.type, i.uri, i.integration_http_method, i.timeout_milliseconds] }
      options = { for k, i in aws_api_gateway_integration.options : k => [i.type, i.request_templates] }
    }
    method_responses      = { for k, m in aws_api_gateway_method_response.options : k => [m.status_code, m.response_parameters] }
    integration_responses = { for k, r in aws_api_gateway_integration_response.options : k => [r.status_code, r.response_parameters] }
    gateway_responses = {
      for k, g in {
        throttled   = aws_api_gateway_gateway_response.throttled
        default_4xx = aws_api_gateway_gateway_response.default_4xx
        default_5xx = aws_api_gateway_gateway_response.default_5xx
      } : k => [g.response_type, g.status_code, g.response_parameters, g.response_templates]
    }
    timeout = var.integration_timeout_ms
  }))
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  # El hash depende del CONTENIDO de lo que define la pasarela (metodos, integraciones, respuestas
  # y plazos), no de identificadores generados: un cambio de origen, de cabeceras o de plantillas
  # vuelve a desplegar la etapa.
  triggers = {
    redeployment = local.api_redeployment_hash
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "live" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api.id
  stage_name    = "live"
}

# Limite de uso global del esqueleto: rafaga 5, tasa sostenida 1 por segundo (scalability-design.md).
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.live.stage_name
  method_path = "*/*"

  settings {
    throttling_rate_limit  = var.throttle_rate_limit
    throttling_burst_limit = var.throttle_burst_limit
  }
}

# ---------------------------------------------------------------------------
# Pantalla: deposito privado de S3 + CloudFront con control de acceso al origen.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "web" {
  bucket_prefix = "${var.name_prefix}-web-"
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket                  = aws_s3_bucket.web.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "web" {
  bucket = aws_s3_bucket.web.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "web" {
  bucket = aws_s3_bucket.web.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "web" {
  name                              = "${var.name_prefix}-web"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  default_root_object = "index.html"
  comment             = "${var.name_prefix} pantalla"

  origin {
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_id                = "web"
    origin_access_control_id = aws_cloudfront_origin_access_control.web.id
  }

  # index.html y el resto: sin cache compartida (el flujo de despliegue publica index.html con
  # no-cache e invalida /index.html). Los archivos con hash de /assets/ llevan cache larga.
  default_cache_behavior {
    target_origin_id           = "web"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled (administrada)
    response_headers_policy_id = aws_cloudfront_response_headers_policy.web.id
  }

  ordered_cache_behavior {
    path_pattern               = "/assets/*"
    target_origin_id           = "web"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized (administrada)
    response_headers_policy_id = aws_cloudfront_response_headers_policy.web.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontRead"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.web.arn}/*"
        Condition = {
          StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.web.arn }
        }
      },
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.web.arn, "${aws_s3_bucket.web.arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      },
    ]
  })
}
