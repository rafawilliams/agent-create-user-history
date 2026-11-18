output "api_url" {
  description = "Direccion base de la API (valor de VITE_API_URL al compilar la pantalla)."
  value       = aws_api_gateway_stage.live.invoke_url
}

output "web_url" {
  description = "Direccion HTTPS de la pantalla (CloudFront)."
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
}

output "web_bucket" {
  description = "Deposito privado de S3 con los archivos de la pantalla."
  value       = aws_s3_bucket.web.id
}

output "lambda_function_name" {
  value = aws_lambda_function.story.function_name
}

output "model_invocation_logging" {
  description = "El registro de invocaciones del modelo se mantiene DESACTIVADO (NFR4.2): este modulo no crea aws_bedrock_model_invocation_logging_configuration."
  value       = "disabled"
}

# Valores publicos (sin secretos) que alimentan las variables VITE_ de la pantalla.
output "cognito_region" {
  description = "Valor de VITE_COGNITO_REGION."
  value       = var.region
}

output "cognito_user_pool_id" {
  description = "Valor de VITE_COGNITO_USER_POOL_ID."
  value       = aws_cognito_user_pool.main.id
}

output "cognito_domain" {
  description = "Valor de VITE_COGNITO_DOMAIN (host del dominio alojado, sin esquema)."
  value       = "${aws_cognito_user_pool_domain.main.domain}.auth.${var.region}.amazoncognito.com"
}

output "cognito_client_id" {
  description = "Valor de VITE_COGNITO_CLIENT_ID."
  value       = aws_cognito_user_pool_client.web.id
}

output "web_distribution_id" {
  description = "Identificador de la distribucion (deploy.yml invalida /index.html tras publicar)."
  value       = aws_cloudfront_distribution.web.id
}

output "api_redeployment_hash" {
  description = "Hash del contenido de la pasarela que dispara el redespliegue de la etapa (diagnostico y pruebas)."
  value       = local.api_redeployment_hash
}
