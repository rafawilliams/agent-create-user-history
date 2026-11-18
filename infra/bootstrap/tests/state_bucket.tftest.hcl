# Paso 12 (arranque): deposito de estado y proveedor OIDC (NFR5.6, NFR5.2). Sin AWS.
mock_provider "aws" {}

variables {
  github_repository = "example-org/example-repo"
  state_bucket_name = "example-ba-agent-tfstate-123456789012"
}

override_data {
  override_during = plan
  target          = data.aws_caller_identity.current
  values = {
    account_id = "123456789012"
  }
}

run "state_bucket_uses_the_given_name_and_never_force_destroys" {
  command = plan

  assert {
    condition     = aws_s3_bucket.state.bucket == "example-ba-agent-tfstate-123456789012" && aws_s3_bucket.state.force_destroy == false
    error_message = "El deposito de estado lleva el nombre informado y no se borra con objetos."
  }
}

run "state_bucket_blocks_all_public_access" {
  command = plan

  assert {
    condition = alltrue([
      aws_s3_bucket_public_access_block.state.block_public_acls,
      aws_s3_bucket_public_access_block.state.block_public_policy,
      aws_s3_bucket_public_access_block.state.ignore_public_acls,
      aws_s3_bucket_public_access_block.state.restrict_public_buckets,
    ])
    error_message = "El deposito de estado debe ser privado (acceso publico bloqueado)."
  }
}

run "state_bucket_is_versioned_and_encrypted" {
  command = plan

  assert {
    condition = (
      aws_s3_bucket_versioning.state.versioning_configuration[0].status == "Enabled" &&
      one(aws_s3_bucket_server_side_encryption_configuration.state.rule).apply_server_side_encryption_by_default[0].sse_algorithm == "AES256"
    )
    error_message = "El deposito de estado debe tener versionado y cifrado con la clave administrada por S3."
  }
}

run "state_bucket_policy_denies_non_tls_access" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_s3_bucket_policy.state.policy).Statement :
      s.Effect == "Deny" && s.Principal == "*" && s.Action == ["s3:*"] &&
      toset(s.Resource) == toset(["arn:aws:s3:::example-ba-agent-tfstate-123456789012", "arn:aws:s3:::example-ba-agent-tfstate-123456789012/*"]) &&
      s.Condition == { Bool = { "aws:SecureTransport" = "false" } }
    ])
    error_message = "La politica del deposito debe denegar todo acceso sin TLS (bucket y objetos)."
  }
}

run "github_oidc_provider_has_the_sts_audience" {
  command = plan

  assert {
    condition = (
      aws_iam_openid_connect_provider.github.url == "https://token.actions.githubusercontent.com" &&
      aws_iam_openid_connect_provider.github.client_id_list == toset(["sts.amazonaws.com"])
    )
    error_message = "Un proveedor OIDC de GitHub con aud sts.amazonaws.com."
  }
}
