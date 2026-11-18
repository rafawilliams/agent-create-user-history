# Pasos 9 a 11: pasarela y CORS (NFR3.1, NFR1.1, NFR5.9). Proveedor simulado, sin AWS.
mock_provider "aws" {}
mock_provider "archive" {}

variables {
  allowed_emails          = "ana@example.com"
  google_client_id        = "dummy-google-client-id"
  google_client_secret    = "dummy-google-client-secret"
  microsoft_client_id     = "dummy-microsoft-client-id"
  microsoft_client_secret = "dummy-microsoft-client-secret"
}

override_data {
  override_during = plan
  target          = data.aws_caller_identity.current
  values = {
    account_id = "123456789012"
  }
}

override_resource {
  override_during = plan
  target          = aws_cloudfront_distribution.web
  values = {
    id          = "EDFDVBD6EXAMPLE"
    arn         = "arn:aws:cloudfront::123456789012:distribution/EDFDVBD6EXAMPLE"
    domain_name = "d111111abcdef8.cloudfront.net"
  }
}

override_resource {
  override_during = plan
  target          = aws_lambda_alias.live
  values = {
    invoke_arn = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:business-analyst-agent-story-service:live/invocations"
  }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_method.post
  values          = { id = "m-post" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_method.session
  values          = { id = "m-session" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_method.options
  values          = { id = "m-options" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_integration.post
  values          = { id = "i-post" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_integration.session
  values          = { id = "i-session" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_integration.options
  values          = { id = "i-options" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_integration_response.options
  values          = { id = "ir-options" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_gateway_response.throttled
  values          = { id = "gr-throttled" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_gateway_response.default_4xx
  values          = { id = "gr-4xx" }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_gateway_response.default_5xx
  values          = { id = "gr-5xx" }
}

# ---- /v1/session: GET y DELETE hacia la misma integracion (C2) ---------------------------

run "session_resource_exists_under_v1" {
  command = plan

  assert {
    condition     = aws_api_gateway_resource.session.path_part == "session"
    error_message = "Debe existir el recurso /v1/session."
  }
}

run "session_methods_are_get_and_delete_without_gateway_auth" {
  command = plan

  assert {
    condition = (
      aws_api_gateway_method.session["GET"].http_method == "GET" &&
      aws_api_gateway_method.session["DELETE"].http_method == "DELETE" &&
      aws_api_gateway_method.session["GET"].authorization == "NONE" &&
      aws_api_gateway_method.session["DELETE"].authorization == "NONE"
    )
    error_message = "GET y DELETE de /v1/session; la credencial la verifica el servicio (C3)."
  }
}

run "session_methods_use_the_same_lambda_proxy_integration" {
  command = plan

  assert {
    condition = (
      aws_api_gateway_integration.session["GET"].type == "AWS_PROXY" &&
      aws_api_gateway_integration.session["DELETE"].type == "AWS_PROXY" &&
      aws_api_gateway_integration.session["GET"].integration_http_method == "POST" &&
      aws_api_gateway_integration.session["GET"].uri == aws_api_gateway_integration.post.uri &&
      aws_api_gateway_integration.session["DELETE"].uri == aws_api_gateway_integration.post.uri &&
      aws_api_gateway_integration.session["GET"].uri == aws_lambda_alias.live.invoke_arn
    )
    error_message = "Ambos metodos de /v1/session integran con el mismo alias live de la funcion."
  }
}

# ---- Preflight CORS (NFR5.9) -------------------------------------------------------------

run "preflight_exists_on_stories_and_session" {
  command = plan

  assert {
    condition = (
      aws_api_gateway_method.options["stories"].http_method == "OPTIONS" &&
      aws_api_gateway_method.options["session"].http_method == "OPTIONS" &&
      aws_api_gateway_integration.options["stories"].type == "MOCK" &&
      aws_api_gateway_integration.options["session"].type == "MOCK"
    )
    error_message = "El preflight (OPTIONS) debe existir en /v1/stories y en /v1/session."
  }
}

run "preflight_headers_use_exact_origin_methods_and_headers" {
  command = plan

  assert {
    condition = alltrue([
      for key in ["stories", "session"] :
      aws_api_gateway_integration_response.options[key].response_parameters == tomap({
        "method.response.header.Access-Control-Allow-Origin"  = "'https://d111111abcdef8.cloudfront.net'"
        "method.response.header.Access-Control-Allow-Headers" = "'Authorization,Content-Type'"
        "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,DELETE,OPTIONS'"
      })
    ])
    error_message = "El preflight debe responder con el origen exacto, GET,POST,DELETE,OPTIONS y Authorization,Content-Type."
  }
}

run "preflight_never_uses_a_wildcard_origin" {
  command = plan

  assert {
    condition = alltrue([
      for key in ["stories", "session"] :
      !strcontains(aws_api_gateway_integration_response.options[key].response_parameters["method.response.header.Access-Control-Allow-Origin"], "*")
    ])
    error_message = "El origen permitido no puede ser un comodin."
  }
}

# ---- Respuestas de error de la pasarela --------------------------------------------------

run "gateway_error_responses_carry_the_origin_header" {
  command = plan

  assert {
    condition = alltrue([
      aws_api_gateway_gateway_response.throttled.response_type == "THROTTLED",
      aws_api_gateway_gateway_response.default_4xx.response_type == "DEFAULT_4XX",
      aws_api_gateway_gateway_response.default_5xx.response_type == "DEFAULT_5XX",
      aws_api_gateway_gateway_response.throttled.response_parameters["gatewayresponse.header.Access-Control-Allow-Origin"] == "'https://d111111abcdef8.cloudfront.net'",
      aws_api_gateway_gateway_response.default_4xx.response_parameters["gatewayresponse.header.Access-Control-Allow-Origin"] == "'https://d111111abcdef8.cloudfront.net'",
      aws_api_gateway_gateway_response.default_5xx.response_parameters["gatewayresponse.header.Access-Control-Allow-Origin"] == "'https://d111111abcdef8.cloudfront.net'",
    ])
    error_message = "THROTTLED, DEFAULT_4XX y DEFAULT_5XX deben llevar la cabecera de origen exacta."
  }
}

run "throttled_response_keeps_the_c1_error_shape" {
  command = plan

  assert {
    condition = (
      aws_api_gateway_gateway_response.throttled.status_code == "429" &&
      jsondecode(aws_api_gateway_gateway_response.throttled.response_templates["application/json"]).code == "RATE_LIMITED"
    )
    error_message = "El 429 debe conservar el cuerpo RATE_LIMITED de C1."
  }
}

# ---- Plazos y limites (NFR1.1, NFR3.1) ---------------------------------------------------

run "timeouts_are_chained_55_57_58" {
  command = plan

  assert {
    condition = (
      aws_lambda_function.story.timeout == 57 &&
      aws_api_gateway_integration.post.timeout_milliseconds == 58000 &&
      aws_api_gateway_integration.session["GET"].timeout_milliseconds == 58000 &&
      aws_api_gateway_integration.session["DELETE"].timeout_milliseconds == 58000
    )
    error_message = "Funcion 57 s e integracion 58 000 ms (el servicio de 55 s esta en el codigo)."
  }
}

run "usage_limits_and_reserved_concurrency" {
  command = plan

  assert {
    condition = (
      aws_api_gateway_method_settings.all.settings[0].throttling_rate_limit == 1 &&
      aws_api_gateway_method_settings.all.settings[0].throttling_burst_limit == 5 &&
      aws_lambda_function.story.reserved_concurrent_executions == 5
    )
    error_message = "1 solicitud por segundo, rafaga de 5 y concurrencia reservada de 5."
  }
}

# ---- Redespliegue (el hash depende del CONTENIDO de la configuracion, no de ids) ----------

run "deployment_hash_baseline" {
  command = plan

  assert {
    condition     = length(aws_api_gateway_deployment.api.triggers["redeployment"]) == 40
    error_message = "El despliegue debe tener un hash de redespliegue conocido."
  }
}

run "deployment_hash_changes_when_the_allowed_origin_changes" {
  command = plan

  override_resource {
    override_during = plan
    target          = aws_cloudfront_distribution.web
    values = {
      id          = "EDFDVBD6EXAMPLE"
      arn         = "arn:aws:cloudfront::123456789012:distribution/EDFDVBD6EXAMPLE"
      domain_name = "d222222abcdef8.cloudfront.net"
    }
  }

  assert {
    condition     = aws_api_gateway_deployment.api.triggers["redeployment"] != run.deployment_hash_baseline.api_redeployment_hash
    error_message = "Cambiar el origen permitido (preflight y respuestas de error) debe volver a desplegar la etapa."
  }
}

run "deployment_hash_changes_when_the_integration_timeout_changes" {
  command = plan

  variables {
    integration_timeout_ms = 50000
  }

  assert {
    condition     = aws_api_gateway_deployment.api.triggers["redeployment"] != run.deployment_hash_baseline.api_redeployment_hash
    error_message = "Cambiar el tiempo de la integracion debe volver a desplegar la etapa."
  }
}

run "deployment_hash_ignores_generated_ids" {
  command = plan

  override_resource {
    override_during = plan
    target          = aws_api_gateway_integration.post
    values          = { id = "otro-id" }
  }

  override_resource {
    override_during = plan
    target          = aws_api_gateway_gateway_response.default_4xx
    values          = { id = "otro-id-4xx" }
  }

  assert {
    condition     = aws_api_gateway_deployment.api.triggers["redeployment"] == run.deployment_hash_baseline.api_redeployment_hash
    error_message = "El hash debe depender del contenido, no de identificadores generados."
  }
}
