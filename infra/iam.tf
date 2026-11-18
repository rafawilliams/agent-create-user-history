# Rol de ejecucion de la funcion (NFR5.5): politica escrita con jsonencode, sin IAM, Cognito ni S3.
# El rol lleva el limite de permisos de infra/bootstrap (NFR5.4); sin el, el rol de aplicacion no
# puede crearlo (iam:CreateRole exige la condicion iam:PermissionsBoundary).

resource "aws_iam_role" "story" {
  name                 = "${local.function_name}-exec"
  permissions_boundary = local.permissions_boundary_arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "story" {
  name = "minimal-access"
  role = aws_iam_role.story.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "Logs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = ["${aws_cloudwatch_log_group.story.arn}:*"]
      },
      {
        # Perfil de inferencia exacto y modelo base con region comodin (el perfil enruta entre
        # regiones), ambos derivados de bedrock_model_id (unica fuente, NFR5.2).
        Sid      = "InvokeModel"
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = local.model_arns
      },
    ]
  })
}
