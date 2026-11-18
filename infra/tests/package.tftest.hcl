# Paso 20/21: el archivo de la funcion sale de la carpeta de empaquetado (codigo del servicio mas
# dependencias instaladas para Lambda), no de backend/ a secas: sin PyJWT[crypto] el arranque falla.
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

run "lambda_zip_is_built_from_the_package_directory" {
  command = plan

  assert {
    condition = (
      endswith(data.archive_file.story_service.source_dir, "/build/package") &&
      !strcontains(data.archive_file.story_service.source_dir, "backend") &&
      data.archive_file.story_service.type == "zip"
    )
    error_message = "El zip de la funcion debe salir de infra/build/package, no de backend/."
  }
}

run "lambda_zip_does_not_exclude_the_dependencies" {
  command = plan

  assert {
    condition     = !contains(tolist(data.archive_file.story_service.excludes), "requirements*.txt") && !contains(tolist(data.archive_file.story_service.excludes), "*.toml")
    error_message = "Las exclusiones antiguas de backend/ no aplican al paquete ya construido."
  }
}

run "lambda_handler_is_in_the_top_level_story_service_package" {
  command = plan

  assert {
    condition     = aws_lambda_function.story.handler == "story_service.handler.lambda_handler"
    error_message = "story_service/ debe ser un paquete de nivel superior del zip."
  }
}
