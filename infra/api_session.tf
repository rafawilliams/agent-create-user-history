# /v1/session (C2): GET y DELETE hacia la misma funcion (alias live), y las respuestas de error
# por defecto de la pasarela con la cabecera de origen (NFR5.9). La credencial de sesion la
# verifica el servicio (C3), no la pasarela.

resource "aws_api_gateway_resource" "session" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "session"
}

resource "aws_api_gateway_method" "session" {
  for_each = toset(["GET", "DELETE"])

  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.session.id
  http_method   = each.key
  authorization = "NONE"

  request_validator_id = aws_api_gateway_request_validator.params.id
}

resource "aws_api_gateway_integration" "session" {
  for_each = aws_api_gateway_method.session

  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.session.id
  http_method             = each.value.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_alias.live.invoke_arn
  timeout_milliseconds    = var.integration_timeout_ms
}

# Los errores que genera la propia pasarela (400, 403, 5xx) tambien llevan el origen exacto, para
# que la pantalla pueda leerlos (NFR5.9). El 429 (THROTTLED) esta en main.tf.
resource "aws_api_gateway_gateway_response" "default_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'${local.web_origin}'"
  }
}

resource "aws_api_gateway_gateway_response" "default_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin" = "'${local.web_origin}'"
  }
}
