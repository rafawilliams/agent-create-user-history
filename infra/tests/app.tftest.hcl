# Pasos 14 a 16: Cognito (NFR5.8), pantalla (NFR5.9), rol de la funcion (NFR5.5), registros
# (NFR4.2) y variables de entorno de la funcion (NFR5.2). Proveedor simulado, sin AWS.
mock_provider "aws" {}
mock_provider "archive" {}

variables {
  allowed_emails          = "ana@example.com,luis@example.com"
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
  target          = aws_cloudfront_response_headers_policy.web
  values = {
    id = "5cc3b908-e619-4b99-88e5-2cf7f45965bd"
  }
}

override_resource {
  override_during = plan
  target          = aws_s3_bucket.web
  values = {
    id  = "business-analyst-agent-web-20260101000000000000000001"
    arn = "arn:aws:s3:::business-analyst-agent-web-20260101000000000000000001"
  }
}

override_resource {
  override_during = plan
  target          = aws_api_gateway_rest_api.api
  values = {
    id            = "abc123defg"
    execution_arn = "arn:aws:execute-api:us-east-1:123456789012:abc123defg"
  }
}

override_resource {
  override_during = plan
  target          = aws_cloudwatch_log_group.story
  values = {
    arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/business-analyst-agent-story-service"
  }
}

override_resource {
  override_during = plan
  target          = aws_cognito_user_pool.main
  values = {
    id = "us-east-1_ExamplePool"
  }
}

override_resource {
  override_during = plan
  target          = aws_cognito_user_pool_client.web
  values = {
    id = "exampleclientid123"
  }
}

# ---- Cognito (NFR5.8) --------------------------------------------------------------------

run "user_pool_has_no_self_sign_up_and_is_deletion_protected" {
  command = plan

  assert {
    condition = (
      aws_cognito_user_pool.main.admin_create_user_config[0].allow_admin_create_user_only == true &&
      aws_cognito_user_pool.main.deletion_protection == "ACTIVE"
    )
    error_message = "Sin registro propio y con proteccion contra eliminacion."
  }
}

run "app_client_is_public_code_flow_only" {
  command = plan

  assert {
    condition = (
      aws_cognito_user_pool_client.web.generate_secret == false &&
      aws_cognito_user_pool_client.web.allowed_oauth_flows_user_pool_client == true &&
      aws_cognito_user_pool_client.web.allowed_oauth_flows == toset(["code"]) &&
      aws_cognito_user_pool_client.web.allowed_oauth_scopes == toset(["openid", "email"])
    )
    error_message = "Cliente publico sin secreto y solo el flujo de codigo (PKCE)."
  }
}

run "app_client_federates_only_google_and_microsoft" {
  command = plan

  assert {
    condition     = aws_cognito_user_pool_client.web.supported_identity_providers == toset(["Google", "Microsoft"])
    error_message = "Solo los proveedores Google y Microsoft (sin el grupo propio COGNITO)."
  }
}

run "app_client_token_lifetimes_are_eight_hours_and_revocation_is_on" {
  command = plan

  assert {
    condition = (
      aws_cognito_user_pool_client.web.id_token_validity == 8 &&
      aws_cognito_user_pool_client.web.access_token_validity == 8 &&
      aws_cognito_user_pool_client.web.refresh_token_validity == 8 &&
      aws_cognito_user_pool_client.web.token_validity_units[0].id_token == "hours" &&
      aws_cognito_user_pool_client.web.token_validity_units[0].access_token == "hours" &&
      aws_cognito_user_pool_client.web.token_validity_units[0].refresh_token == "hours" &&
      aws_cognito_user_pool_client.web.enable_token_revocation == true
    )
    error_message = "Vigencias de 8 horas y revocacion de tokens de renovacion."
  }
}

run "app_client_callback_and_logout_are_the_exact_distribution_root" {
  command = plan

  assert {
    condition = (
      aws_cognito_user_pool_client.web.callback_urls == toset(["https://d111111abcdef8.cloudfront.net/"]) &&
      aws_cognito_user_pool_client.web.logout_urls == toset(["https://d111111abcdef8.cloudfront.net/"])
    )
    error_message = "Retorno y cierre de sesion solo con la raiz de la distribucion."
  }
}

run "identity_providers_are_named_google_and_microsoft_with_email_mapping" {
  command = plan

  assert {
    condition = (
      aws_cognito_identity_provider.google.provider_name == "Google" &&
      aws_cognito_identity_provider.google.provider_type == "Google" &&
      aws_cognito_identity_provider.microsoft.provider_name == "Microsoft" &&
      aws_cognito_identity_provider.microsoft.provider_type == "OIDC" &&
      aws_cognito_identity_provider.google.attribute_mapping["email"] == "email" &&
      aws_cognito_identity_provider.google.attribute_mapping["email_verified"] == "email_verified" &&
      aws_cognito_identity_provider.microsoft.attribute_mapping["email"] == "email" &&
      aws_cognito_identity_provider.microsoft.attribute_mapping["email_verified"] == "email_verified"
    )
    error_message = "Proveedores Google y Microsoft con el mapeo de email y email_verified."
  }
}

run "hosted_domain_uses_the_fixed_prefix" {
  command = plan

  assert {
    condition = (
      aws_cognito_user_pool_domain.main.domain == var.cognito_domain_prefix &&
      output.cognito_domain == "${var.cognito_domain_prefix}.auth.us-east-1.amazoncognito.com"
    )
    error_message = "El dominio alojado usa el prefijo fijo."
  }
}

# ---- Pantalla (NFR5.9) -------------------------------------------------------------------

run "content_security_policy_is_exact" {
  command = plan

  assert {
    condition = one(aws_cloudfront_response_headers_policy.web.security_headers_config[0].content_security_policy).content_security_policy == join("; ", [
      "default-src 'self'",
      "script-src 'self'",
      "style-src 'self' 'unsafe-inline'",
      "connect-src 'self' https://abc123defg.execute-api.us-east-1.amazonaws.com https://${var.cognito_domain_prefix}.auth.us-east-1.amazoncognito.com https://cognito-idp.us-east-1.amazonaws.com",
      "img-src 'self' data:",
      "font-src 'self' data:",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ])
    error_message = "La politica de contenido debe ser exactamente la de NFR5.4 de u5."
  }
}

run "security_headers_are_set_and_override_the_origin" {
  command = plan

  assert {
    condition = (
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].content_security_policy[0].override == true &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].strict_transport_security[0].override == true &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].strict_transport_security[0].access_control_max_age_sec >= 31536000 &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].strict_transport_security[0].include_subdomains == true &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].content_type_options[0].override == true &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].referrer_policy[0].override == true &&
      aws_cloudfront_response_headers_policy.web.security_headers_config[0].referrer_policy[0].referrer_policy == "no-referrer"
    )
    error_message = "HSTS, X-Content-Type-Options y Referrer-Policy, todas con override."
  }
}

run "cache_is_by_file_type_and_headers_policy_is_attached" {
  command = plan

  assert {
    condition = (
      aws_cloudfront_distribution.web.default_root_object == "index.html" &&
      aws_cloudfront_distribution.web.default_cache_behavior[0].cache_policy_id == "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" &&
      one(aws_cloudfront_distribution.web.ordered_cache_behavior).path_pattern == "/assets/*" &&
      one(aws_cloudfront_distribution.web.ordered_cache_behavior).cache_policy_id == "658327ea-f89d-4fab-a63d-7e88639e58f6" &&
      aws_cloudfront_distribution.web.default_cache_behavior[0].viewer_protocol_policy == "redirect-to-https" &&
      one(aws_cloudfront_distribution.web.ordered_cache_behavior).viewer_protocol_policy == "redirect-to-https"
    )
    error_message = "index.html sin cache compartida, /assets/* con cache larga y HTTPS con redireccion."
  }
}

run "response_headers_policy_is_attached_to_every_behavior" {
  command = plan

  assert {
    condition = (
      aws_cloudfront_distribution.web.default_cache_behavior[0].response_headers_policy_id == aws_cloudfront_response_headers_policy.web.id &&
      one(aws_cloudfront_distribution.web.ordered_cache_behavior).response_headers_policy_id == aws_cloudfront_response_headers_policy.web.id
    )
    error_message = "Todos los comportamientos llevan la politica de cabeceras."
  }
}

run "web_bucket_is_private_encrypted_and_readable_only_through_the_distribution" {
  command = plan

  assert {
    condition = (
      aws_s3_bucket_public_access_block.web.block_public_acls &&
      aws_s3_bucket_public_access_block.web.block_public_policy &&
      aws_s3_bucket_public_access_block.web.ignore_public_acls &&
      aws_s3_bucket_public_access_block.web.restrict_public_buckets &&
      one(aws_s3_bucket_server_side_encryption_configuration.web.rule).apply_server_side_encryption_by_default[0].sse_algorithm == "AES256" &&
      aws_cloudfront_origin_access_control.web.signing_behavior == "always" &&
      anytrue([
        for s in jsondecode(aws_s3_bucket_policy.web.policy).Statement :
        s.Effect == "Allow" && s.Principal == { Service = "cloudfront.amazonaws.com" } && s.Action == "s3:GetObject" &&
        s.Condition == { StringEquals = { "AWS:SourceArn" = "arn:aws:cloudfront::123456789012:distribution/EDFDVBD6EXAMPLE" } }
      ])
    )
    error_message = "Deposito privado, cifrado y legible solo desde la distribucion (control de acceso al origen)."
  }
}

run "distribution_and_bucket_keep_no_access_logs" {
  command = plan

  assert {
    condition     = length(aws_cloudfront_distribution.web.logging_config) == 0
    error_message = "La distribucion no guarda registros de acceso (NFR4.2)."
  }
}

# ---- Rol de la funcion (NFR5.5) ----------------------------------------------------------

run "function_role_policy_is_exactly_logs_and_the_configured_model" {
  command = plan

  assert {
    condition = (
      anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
        s.Sid == "Logs" && s.Effect == "Allow" && toset(s.Action) == toset(["logs:CreateLogStream", "logs:PutLogEvents"]) &&
      s.Resource == ["arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/business-analyst-agent-story-service:*"]]) &&
      anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
        s.Sid == "InvokeModel" && s.Effect == "Allow" && s.Action == ["bedrock:InvokeModel"] &&
        toset(s.Resource) == toset([
          "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-sonnet-4-6",
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6",
        ])
      ]) &&
      length(jsondecode(aws_iam_role_policy.story.policy).Statement) == 2
    )
    error_message = "Solo escribir sus registros e invocar el perfil y el modelo base configurados."
  }
}

run "function_role_has_no_iam_cognito_or_s3_permissions" {
  command = plan

  assert {
    condition = alltrue([
      for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      alltrue([for a in s.Action : a == "bedrock:InvokeModel" || startswith(a, "logs:")])
    ])
    error_message = "La funcion no puede tener permisos de IAM, Cognito ni S3."
  }
}

run "function_role_carries_the_permissions_boundary" {
  command = plan

  assert {
    condition = (
      aws_iam_role.story.permissions_boundary == "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-boundary" &&
      startswith(aws_iam_role.story.name, "business-analyst-agent-")
    )
    error_message = "Todo rol que Terraform crea lleva el limite de permisos y el prefijo de la aplicacion."
  }
}

# ---- Variables de entorno y registros ----------------------------------------------------

run "function_environment_has_the_identity_settings_and_no_simulated_session" {
  command = plan

  assert {
    condition = (
      nonsensitive(aws_lambda_function.story.environment[0].variables["CORS_ALLOWED_ORIGIN"]) == "https://d111111abcdef8.cloudfront.net" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["COGNITO_REGION"]) == "us-east-1" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["COGNITO_USER_POOL_ID"]) == "us-east-1_ExamplePool" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["COGNITO_APP_CLIENT_ID"]) == "exampleclientid123" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["ALLOWED_EMAILS"]) == "ana@example.com,luis@example.com" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["APP_ENV"]) == "prod" &&
      nonsensitive(aws_lambda_function.story.environment[0].variables["BEDROCK_MODEL_ID"]) == "us.anthropic.claude-sonnet-4-6" &&
      !contains(keys(nonsensitive(aws_lambda_function.story.environment[0].variables)), "ALLOW_SIMULATED_SESSION")
    )
    error_message = "Variables de entorno de la funcion (NFR5.2): identidad y correos, sin ALLOW_SIMULATED_SESSION."
  }
}

run "function_log_group_keeps_fourteen_days" {
  command = plan

  assert {
    condition     = aws_cloudwatch_log_group.story.retention_in_days == 14
    error_message = "Retencion de 14 dias (NFR4.2)."
  }
}

# ---- Salidas -----------------------------------------------------------------------------

run "cognito_outputs_feed_the_web_build" {
  command = plan

  assert {
    condition = (
      output.cognito_region == "us-east-1" &&
      output.cognito_user_pool_id == "us-east-1_ExamplePool" &&
      output.cognito_client_id == "exampleclientid123" &&
      output.cognito_domain == "${var.cognito_domain_prefix}.auth.us-east-1.amazoncognito.com"
    )
    error_message = "Salidas de Cognito para las variables VITE_ de la pantalla."
  }
}

run "distribution_id_output_feeds_the_cache_invalidation" {
  command = plan

  assert {
    condition     = output.web_distribution_id == "EDFDVBD6EXAMPLE"
    error_message = "deploy.yml necesita el identificador de la distribucion para invalidar /index.html."
  }
}

# ---- Modelo base: solo se quitan los prefijos explicitos us. y global. -------------------

run "model_arns_strip_the_us_prefix" {
  command = plan

  variables {
    bedrock_model_id = "us.anthropic.claude-sonnet-4-6"
  }

  assert {
    condition = anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      s.Sid == "InvokeModel" && toset(s.Resource) == toset([
        "arn:aws:bedrock:us-east-1:123456789012:inference-profile/us.anthropic.claude-sonnet-4-6",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6",
    ])])
    error_message = "us. se quita del modelo base."
  }
}

run "model_arns_strip_the_global_prefix" {
  command = plan

  variables {
    bedrock_model_id = "global.anthropic.claude-sonnet-4-6"
  }

  assert {
    condition = anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      s.Sid == "InvokeModel" && toset(s.Resource) == toset([
        "arn:aws:bedrock:us-east-1:123456789012:inference-profile/global.anthropic.claude-sonnet-4-6",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6",
    ])])
    error_message = "global. se quita del modelo base."
  }
}

run "model_arns_keep_an_unprefixed_anthropic_id" {
  command = plan

  variables {
    bedrock_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
  }

  assert {
    condition = anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      s.Sid == "InvokeModel" && contains(s.Resource, "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0")
    ])
    error_message = "Sin prefijo, el identificador de Anthropic no se recorta."
  }
}

run "model_arns_keep_an_unprefixed_titan_id" {
  command = plan

  variables {
    bedrock_model_id = "amazon.titan-text-express-v1"
  }

  assert {
    condition = anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      s.Sid == "InvokeModel" && contains(s.Resource, "arn:aws:bedrock:*::foundation-model/amazon.titan-text-express-v1")
    ])
    error_message = "Sin prefijo, amazon.titan-* no pierde su primer segmento."
  }
}

run "model_arns_strip_the_us_prefix_of_titan" {
  command = plan

  variables {
    bedrock_model_id = "us.amazon.titan-text-express-v1"
  }

  assert {
    condition = anytrue([for s in jsondecode(aws_iam_role_policy.story.policy).Statement :
      s.Sid == "InvokeModel" && contains(s.Resource, "arn:aws:bedrock:*::foundation-model/amazon.titan-text-express-v1")
    ])
    error_message = "us.amazon.titan-* se recorta solo el prefijo us."
  }
}
