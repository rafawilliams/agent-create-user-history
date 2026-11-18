# Pasos 3 a 5 (raiz de arranque): validaciones de github_repository y state_bucket_name.
mock_provider "aws" {}

variables {
  github_repository = "example-org/example-repo"
  state_bucket_name = "example-ba-agent-tfstate-123456789012"
}

run "github_repository_accepts_owner_repo" {
  command = plan

  assert {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Debe aceptar <organizacion>/<repositorio>."
  }
}

run "github_repository_rejects_missing_slash" {
  command = plan

  variables {
    github_repository = "example-repo"
  }

  expect_failures = [var.github_repository]
}

run "github_repository_rejects_wildcard" {
  command = plan

  variables {
    github_repository = "example-org/*"
  }

  expect_failures = [var.github_repository]
}

run "github_repository_rejects_extra_segments" {
  command = plan

  variables {
    github_repository = "example-org/example-repo/extra"
  }

  expect_failures = [var.github_repository]
}

run "state_bucket_name_accepts_valid_name" {
  command = plan

  assert {
    condition     = length(var.state_bucket_name) >= 3 && length(var.state_bucket_name) <= 63
    error_message = "Debe aceptar un nombre de deposito valido."
  }
}

run "state_bucket_name_rejects_uppercase" {
  command = plan

  variables {
    state_bucket_name = "Example-Bucket"
  }

  expect_failures = [var.state_bucket_name]
}

run "state_bucket_name_rejects_too_short" {
  command = plan

  variables {
    state_bucket_name = "ab"
  }

  expect_failures = [var.state_bucket_name]
}

run "region_rejects_other_regions" {
  command = plan

  variables {
    region = "eu-west-1"
  }

  expect_failures = [var.region]
}
