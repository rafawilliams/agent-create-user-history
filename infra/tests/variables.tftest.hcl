# Pasos 3 a 5: variables y validaciones (NFR5.1, NFR4.3, NFR5.5 origen unico del modelo).
# Todo con proveedor simulado y valores ficticios: nunca se llama a AWS.
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

# ---- allowed_emails (NFR4.3) -------------------------------------------------------------

run "allowed_emails_accepts_one" {
  command = plan

  variables {
    allowed_emails = "ana@example.com"
  }

  assert {
    condition     = length(split(",", var.allowed_emails)) == 1
    error_message = "Debe aceptar un solo correo."
  }
}

run "allowed_emails_accepts_fifty" {
  command = plan

  variables {
    allowed_emails = join(",", [for i in range(50) : "user${i}@example.com"])
  }

  assert {
    condition     = length(split(",", var.allowed_emails)) == 50
    error_message = "Debe aceptar exactamente 50 correos."
  }
}

run "allowed_emails_rejects_fifty_one" {
  command = plan

  variables {
    allowed_emails = join(",", [for i in range(51) : "user${i}@example.com"])
  }

  expect_failures = [var.allowed_emails]
}

run "allowed_emails_rejects_uppercase" {
  command = plan

  variables {
    allowed_emails = "Ana@example.com"
  }

  expect_failures = [var.allowed_emails]
}

run "allowed_emails_rejects_invalid_format" {
  command = plan

  variables {
    allowed_emails = "not-an-email"
  }

  expect_failures = [var.allowed_emails]
}

run "allowed_emails_rejects_empty" {
  command = plan

  variables {
    allowed_emails = ""
  }

  expect_failures = [var.allowed_emails]
}

run "allowed_emails_rejects_empty_entry" {
  command = plan

  variables {
    allowed_emails = "ana@example.com,,luis@example.com"
  }

  expect_failures = [var.allowed_emails]
}

run "allowed_emails_rejects_spaces" {
  command = plan

  variables {
    allowed_emails = "ana@example.com, luis@example.com"
  }

  expect_failures = [var.allowed_emails]
}

# ---- Sensibilidad (NFR5.1) ---------------------------------------------------------------

run "secret_variables_are_sensitive" {
  command = plan

  assert {
    condition = alltrue([
      issensitive(var.allowed_emails),
      issensitive(var.google_client_id),
      issensitive(var.google_client_secret),
      issensitive(var.microsoft_client_id),
      issensitive(var.microsoft_client_secret),
    ])
    error_message = "Las variables de secretos y de correos deben ser sensitive (NFR5.1)."
  }
}

# ---- cognito_domain_prefix ---------------------------------------------------------------

run "cognito_domain_prefix_default_is_valid" {
  command = plan

  assert {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$", var.cognito_domain_prefix))
    error_message = "El prefijo por defecto debe cumplir el formato de dominio de Cognito."
  }
}

run "cognito_domain_prefix_rejects_uppercase" {
  command = plan

  variables {
    cognito_domain_prefix = "Business-Agent"
  }

  expect_failures = [var.cognito_domain_prefix]
}

run "cognito_domain_prefix_rejects_reserved_word" {
  command = plan

  variables {
    cognito_domain_prefix = "my-cognito-app"
  }

  expect_failures = [var.cognito_domain_prefix]
}

# ---- bedrock_model_id (se mantiene) ------------------------------------------------------

run "bedrock_model_id_accepts_inference_profile" {
  command = plan

  variables {
    bedrock_model_id = "us.anthropic.claude-sonnet-4-6"
  }

  assert {
    condition     = var.bedrock_model_id == "us.anthropic.claude-sonnet-4-6"
    error_message = "Debe aceptar un perfil de inferencia de Anthropic."
  }
}

run "bedrock_model_id_rejects_other_providers" {
  command = plan

  variables {
    bedrock_model_id = "openai.gpt-4"
  }

  expect_failures = [var.bedrock_model_id]
}

run "bedrock_model_id_rejects_wildcards" {
  command = plan

  variables {
    bedrock_model_id = "anthropic.claude-*"
  }

  expect_failures = [var.bedrock_model_id]
}

# ---- region (el arranque y las politicas estan fijos en us-east-1) -----------------------

run "region_accepts_us_east_1" {
  command = plan

  assert {
    condition     = var.region == "us-east-1"
    error_message = "us-east-1 es la region del proyecto."
  }
}

run "region_rejects_other_regions" {
  command = plan

  variables {
    region = "eu-west-1"
  }

  expect_failures = [var.region]
}
