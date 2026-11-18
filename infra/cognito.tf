# Cognito (u4): grupo de usuarios sin registro propio, dominio alojado, federaciones con Google y
# Microsoft y un cliente publico con flujo de codigo y PKCE (NFR5.8). Los secretos de las
# federaciones llegan por variables sensibles (NFR5.1).

resource "aws_cognito_user_pool" "main" {
  name                = "${var.name_prefix}-users"
  deletion_protection = "ACTIVE"

  # Sin registro propio: las cuentas entran solo por las federaciones permitidas.
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

# El prefijo es fijo para conocer de antemano la direccion de retorno que Google y Microsoft piden.
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "openid email"
  }

  attribute_mapping = {
    email          = "email"
    email_verified = "email_verified"
  }
}

resource "aws_cognito_identity_provider" "microsoft" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Microsoft"
  provider_type = "OIDC"

  provider_details = {
    client_id                 = var.microsoft_client_id
    client_secret             = var.microsoft_client_secret
    authorize_scopes          = "openid email"
    oidc_issuer               = "https://login.microsoftonline.com/${var.microsoft_tenant_id}/v2.0"
    attributes_request_method = "GET"
  }

  attribute_mapping = {
    email          = "email"
    email_verified = "email_verified"
  }
}

# Cliente publico (sin secreto): codigo con PKCE; retorno y cierre solo con la raiz exacta de la
# distribucion (la pantalla usa `<origen>/`).
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.name_prefix}-web"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email"]
  supported_identity_providers         = ["Google", "Microsoft"]

  callback_urls = ["${local.web_origin}/"]
  logout_urls   = ["${local.web_origin}/"]

  explicit_auth_flows           = ["ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  id_token_validity      = 8
  access_token_validity  = 8
  refresh_token_validity = 8

  token_validity_units {
    id_token      = "hours"
    access_token  = "hours"
    refresh_token = "hours"
  }

  depends_on = [
    aws_cognito_identity_provider.google,
    aws_cognito_identity_provider.microsoft,
  ]
}
