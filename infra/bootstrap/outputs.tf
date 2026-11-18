output "state_bucket" {
  description = "Deposito de estado: valor de la variable de GitHub STATE_BUCKET_NAME."
  value       = aws_s3_bucket.state.id
}

output "plan_role_arn" {
  description = "Valor de la variable de GitHub AWS_PLAN_ROLE_ARN."
  value       = aws_iam_role.plan.arn
}

output "apply_role_arn" {
  description = "Valor de la variable de GitHub AWS_APPLY_ROLE_ARN."
  value       = aws_iam_role.apply.arn
}

output "permissions_boundary_arn" {
  description = "Limite de permisos que llevan el rol de aplicacion y todo rol que Terraform cree."
  value       = aws_iam_policy.boundary.arn
}

output "oidc_provider_arn" {
  description = "Proveedor OIDC de GitHub."
  value       = aws_iam_openid_connect_provider.github.arn
}
