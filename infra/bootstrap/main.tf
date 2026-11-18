# Raiz de arranque (se aplica una vez, a mano, con credenciales administrativas de la persona).
# Crea lo que gobierna a la canalizacion: el deposito de estado, el proveedor OIDC de GitHub, el
# limite de permisos y los roles de plan y de aplicacion. El rol de aplicacion no puede modificar
# nada de esta raiz (NFR5.4): quien controla la canalizacion no controla las identidades que la
# gobiernan. Todas las politicas se escriben con jsonencode (convencion de verificacion de u6).

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = var.region

  # Prefijo de nombre de los recursos y de los roles de la APLICACION (los que el rol de aplicacion
  # puede crear y administrar). Los roles del arranque NO lo llevan, a proposito.
  app_role_arn_pattern = "arn:aws:iam::${local.account_id}:role/${var.name_prefix}-*"

  plan_role_name      = "pipeline-${var.name_prefix}-plan"
  apply_role_name     = "pipeline-${var.name_prefix}-apply"
  boundary_name       = "pipeline-${var.name_prefix}-boundary"
  apply_boundary_name = "pipeline-${var.name_prefix}-apply-boundary"

  oidc_host          = "token.actions.githubusercontent.com"
  oidc_arn           = "arn:aws:iam::${local.account_id}:oidc-provider/${local.oidc_host}"
  plan_arn           = "arn:aws:iam::${local.account_id}:role/${local.plan_role_name}"
  apply_arn          = "arn:aws:iam::${local.account_id}:role/${local.apply_role_name}"
  boundary_arn       = "arn:aws:iam::${local.account_id}:policy/${local.boundary_name}"
  apply_boundary_arn = "arn:aws:iam::${local.account_id}:policy/${local.apply_boundary_name}"

  # Estado remoto: la clave coincide con el backend de infra/versions.tf.
  state_bucket_arn = "arn:aws:s3:::${var.state_bucket_name}"
  state_key_prefix = "${var.name_prefix}/"
  state_object_arn = "${local.state_bucket_arn}/${local.state_key_prefix}terraform.tfstate"
  state_lock_arn   = "${local.state_object_arn}.tflock"
  # El backend de Terraform lista el prefijo del estado y el de los espacios de trabajo (env:/).
  state_list_prefixes = [local.state_key_prefix, "${local.state_key_prefix}*", "env:/", "env:/*"]

  # Deposito de la pantalla: usa bucket_prefix, por eso los permisos se acotan con un patron.
  web_bucket_arn_pattern = "arn:aws:s3:::${var.name_prefix}-web-*"
  log_group_arn_pattern  = "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/lambda/${var.name_prefix}-*"
  function_arn_pattern   = "arn:aws:lambda:${local.region}:${local.account_id}:function:${var.name_prefix}-*"
  userpool_arn_pattern   = "arn:aws:cognito-idp:${local.region}:${local.account_id}:userpool/*"

  oidc_trust = { for k, sub in {
    plan  = "repo:${var.github_repository}:pull_request"
    apply = "repo:${var.github_repository}:ref:refs/heads/main"
    } : k => jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect    = "Allow"
        Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${local.oidc_host}:aud" = "sts.amazonaws.com"
            "${local.oidc_host}:sub" = sub
          }
        }
      }]
    })
  }

  state_list_statement = {
    Sid      = "StateListBucket"
    Effect   = "Allow"
    Action   = ["s3:ListBucket"]
    Resource = [local.state_bucket_arn]
    # IfExists: una lectura de un estado o de un .tflock que aun no existe devuelve 404 y no 403.
    Condition = { StringLikeIfExists = { "s3:prefix" = local.state_list_prefixes } }
  }

  deny_statements = [
    {
      Sid    = "DenyBootstrapIam"
      Effect = "Deny"
      Action = ["iam:*"]
      Resource = [
        local.boundary_arn,
        local.apply_boundary_arn,
        local.oidc_arn,
        local.plan_arn,
        local.apply_arn,
      ]
    },
    {
      Sid    = "DenyStateBucketAdmin"
      Effect = "Deny"
      Action = [
        "s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy", "s3:PutBucketVersioning",
        "s3:PutEncryptionConfiguration", "s3:PutBucketPublicAccessBlock",
        "s3:DeleteBucketPublicAccessBlock", "s3:PutBucketAcl", "s3:PutLifecycleConfiguration",
      ]
      Resource = [local.state_bucket_arn]
    },
    {
      Sid      = "DenyBoundaryRemoval"
      Effect   = "Deny"
      Action   = ["iam:DeleteRolePermissionsBoundary"]
      Resource = ["*"]
    },
    {
      # Una politica con permisos amplios no puede crear un rol sin el limite ni cambiar el limite
      # de un rol por otro. Si la clave falta, StringNotEquals se cumple y la denegacion aplica.
      Sid       = "DenyUnboundedRoles"
      Effect    = "Deny"
      Action    = ["iam:CreateRole", "iam:PutRolePermissionsBoundary"]
      Resource  = ["*"]
      Condition = { StringNotEquals = { "iam:PermissionsBoundary" = local.boundary_arn } }
    },
  ]

  # Lo que el rol de aplicacion puede hacer. El limite de permisos lo acota por servicio (abajo).
  apply_allow_statements = [
    local.state_list_statement,
    {
      Sid    = "StateObject"
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
      Resource = [
        local.state_object_arn,
        local.state_lock_arn,
      ]
    },
    {
      Sid    = "Lambda"
      Effect = "Allow"
      Action = [
        "lambda:CreateFunction", "lambda:DeleteFunction", "lambda:GetFunction",
        "lambda:GetFunctionConfiguration", "lambda:GetFunctionCodeSigningConfig",
        "lambda:GetRuntimeManagementConfig", "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration", "lambda:PublishVersion",
        "lambda:ListVersionsByFunction", "lambda:CreateAlias", "lambda:GetAlias",
        "lambda:UpdateAlias", "lambda:DeleteAlias", "lambda:AddPermission",
        "lambda:RemovePermission", "lambda:GetPolicy", "lambda:PutFunctionConcurrency",
        "lambda:DeleteFunctionConcurrency", "lambda:GetFunctionConcurrency", "lambda:ListTags",
        "lambda:TagResource", "lambda:UntagResource",
      ]
      Resource = [local.function_arn_pattern, "${local.function_arn_pattern}:*"]
    },
    {
      Sid      = "ApiGateway"
      Effect   = "Allow"
      Action   = ["apigateway:GET", "apigateway:POST", "apigateway:PUT", "apigateway:PATCH", "apigateway:DELETE"]
      Resource = ["arn:aws:apigateway:${local.region}::/restapis", "arn:aws:apigateway:${local.region}::/restapis/*", "arn:aws:apigateway:${local.region}::/tags/*"]
    },
    {
      Sid    = "WebBucket"
      Effect = "Allow"
      Action = [
        "s3:CreateBucket", "s3:DeleteBucket", "s3:ListBucket", "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy", "s3:PutBucketVersioning", "s3:PutBucketPublicAccessBlock",
        "s3:PutEncryptionConfiguration", "s3:PutBucketTagging", "s3:GetBucketAcl",
        "s3:GetBucketCORS", "s3:GetBucketLocation", "s3:GetBucketLogging",
        "s3:GetBucketObjectLockConfiguration", "s3:GetBucketOwnershipControls",
        "s3:GetBucketPolicy", "s3:GetBucketPublicAccessBlock", "s3:GetBucketRequestPayment",
        "s3:GetBucketTagging", "s3:GetBucketVersioning", "s3:GetBucketWebsite",
        "s3:GetAccelerateConfiguration", "s3:GetEncryptionConfiguration",
        "s3:GetLifecycleConfiguration", "s3:GetReplicationConfiguration",
      ]
      Resource = [local.web_bucket_arn_pattern]
    },
    {
      Sid      = "WebObjects"
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject"]
      Resource = ["${local.web_bucket_arn_pattern}/*"]
    },
    {
      Sid    = "CloudFront"
      Effect = "Allow"
      Action = [
        "cloudfront:CreateDistribution", "cloudfront:GetDistribution", "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution", "cloudfront:TagResource", "cloudfront:UntagResource",
        "cloudfront:ListTagsForResource", "cloudfront:CreateOriginAccessControl",
        "cloudfront:GetOriginAccessControl", "cloudfront:UpdateOriginAccessControl",
        "cloudfront:DeleteOriginAccessControl", "cloudfront:CreateResponseHeadersPolicy",
        "cloudfront:GetResponseHeadersPolicy", "cloudfront:UpdateResponseHeadersPolicy",
        "cloudfront:DeleteResponseHeadersPolicy", "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
      ]
      Resource = ["arn:aws:cloudfront::${local.account_id}:*"]
    },
    {
      Sid      = "CognitoUserPool"
      Effect   = "Allow"
      Action   = ["cognito-idp:DescribeUserPool", "cognito-idp:UpdateUserPool", "cognito-idp:DeleteUserPool", "cognito-idp:CreateUserPoolClient", "cognito-idp:DescribeUserPoolClient", "cognito-idp:UpdateUserPoolClient", "cognito-idp:DeleteUserPoolClient", "cognito-idp:CreateUserPoolDomain", "cognito-idp:DeleteUserPoolDomain", "cognito-idp:CreateIdentityProvider", "cognito-idp:DescribeIdentityProvider", "cognito-idp:UpdateIdentityProvider", "cognito-idp:DeleteIdentityProvider", "cognito-idp:GetUserPoolMfaConfig", "cognito-idp:ListTagsForResource", "cognito-idp:TagResource", "cognito-idp:UntagResource"]
      Resource = [local.userpool_arn_pattern]
    },
    {
      # Estas acciones no admiten un recurso concreto.
      Sid      = "CognitoAccount"
      Effect   = "Allow"
      Action   = ["cognito-idp:CreateUserPool", "cognito-idp:DescribeUserPoolDomain"]
      Resource = ["*"]
    },
    {
      Sid    = "Logs"
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy",
        "logs:DeleteRetentionPolicy", "logs:PutMetricFilter", "logs:DeleteMetricFilter",
        "logs:TagResource", "logs:UntagResource", "logs:ListTagsForResource",
      ]
      Resource = [local.log_group_arn_pattern, "${local.log_group_arn_pattern}:*"]
    },
    {
      Sid      = "LogsDescribe"
      Effect   = "Allow"
      Action   = ["logs:DescribeLogGroups", "logs:DescribeMetricFilters"]
      Resource = ["*"]
    },
    {
      Sid      = "CloudWatchRead"
      Effect   = "Allow"
      Action   = ["cloudwatch:ListMetrics", "cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics"]
      Resource = ["*"]
    },
    {
      Sid      = "IamCreateRole"
      Effect   = "Allow"
      Action   = ["iam:CreateRole"]
      Resource = [local.app_role_arn_pattern]
      # Solo se crean roles que llevan el limite de permisos.
      Condition = { StringEquals = { "iam:PermissionsBoundary" = local.boundary_arn } }
    },
    {
      # Estas acciones no admiten la condicion del limite: se acotan por prefijo del nombre del rol.
      Sid    = "IamManageRoles"
      Effect = "Allow"
      Action = [
        "iam:DeleteRole", "iam:GetRole", "iam:TagRole", "iam:UntagRole", "iam:UpdateRole",
        "iam:UpdateRoleDescription", "iam:AttachRolePolicy", "iam:DetachRolePolicy",
        "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:UpdateAssumeRolePolicy",
        "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies",
        "iam:ListInstanceProfilesForRole",
      ]
      Resource = [local.app_role_arn_pattern]
    },
    {
      Sid       = "IamPassRole"
      Effect    = "Allow"
      Action    = ["iam:PassRole"]
      Resource  = [local.app_role_arn_pattern]
      Condition = { StringEquals = { "iam:PassedToService" = "lambda.amazonaws.com" } }
    },
  ]

  # Familias de modelos que valida bedrock_model_id (anthropic.claude-* y amazon.titan-*, con o sin
  # prefijo us. o global.). El modelo EXACTO lo fija la politica del rol de la funcion (infra/iam.tf);
  # el limite solo acota el techo a esas familias.
  bedrock_model_resources = [
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
    "arn:aws:bedrock:*::foundation-model/amazon.titan-*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/anthropic.claude-*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/us.anthropic.claude-*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/global.anthropic.claude-*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/amazon.titan-*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/us.amazon.titan-*",
  ]

  # Limite de los roles que Terraform crea (funcion): solo registros y el modelo, sin ningun
  # permiso de IAM (los roles de la aplicacion no necesitan ninguno). Un rol con este limite y
  # permisos amplios sigue sin poder crear roles ni tocar IAM.
  boundary_statements = concat(
    [
      { Sid = "FunctionLogs", Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = [local.log_group_arn_pattern, "${local.log_group_arn_pattern}:*"] },
      { Sid = "InvokeBedrockModel", Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = local.bedrock_model_resources },
    ],
    local.deny_statements,
  )

  # Limite del rol de aplicacion (techo de la canalizacion). Politica administrada (tope de 6 144
  # caracteres): acciones por servicio con comodin; la precision esta en la politica del rol.
  apply_boundary_statements = concat(
    [
      local.state_list_statement,
      {
        Sid      = "StateObject"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = [local.state_object_arn, local.state_lock_arn]
      },
      { Sid = "Lambda", Effect = "Allow", Action = ["lambda:*"], Resource = [local.function_arn_pattern, "${local.function_arn_pattern}:*"] },
      { Sid = "ApiGateway", Effect = "Allow", Action = ["apigateway:*"], Resource = ["arn:aws:apigateway:${local.region}::/restapis", "arn:aws:apigateway:${local.region}::/restapis/*", "arn:aws:apigateway:${local.region}::/tags/*"] },
      { Sid = "WebBucket", Effect = "Allow", Action = ["s3:*"], Resource = [local.web_bucket_arn_pattern, "${local.web_bucket_arn_pattern}/*"] },
      { Sid = "CloudFront", Effect = "Allow", Action = ["cloudfront:*"], Resource = ["arn:aws:cloudfront::${local.account_id}:*"] },
      { Sid = "Cognito", Effect = "Allow", Action = ["cognito-idp:*"], Resource = ["*"] },
      { Sid = "Logs", Effect = "Allow", Action = ["logs:*"], Resource = [local.log_group_arn_pattern, "${local.log_group_arn_pattern}:*"] },
      { Sid = "LogsDescribe", Effect = "Allow", Action = ["logs:DescribeLogGroups", "logs:DescribeMetricFilters"], Resource = ["*"] },
      { Sid = "CloudWatchRead", Effect = "Allow", Action = ["cloudwatch:ListMetrics", "cloudwatch:GetMetricData", "cloudwatch:GetMetricStatistics"], Resource = ["*"] },
      {
        Sid       = "IamCreateRole"
        Effect    = "Allow"
        Action    = ["iam:CreateRole"]
        Resource  = [local.app_role_arn_pattern]
        Condition = { StringEquals = { "iam:PermissionsBoundary" = local.boundary_arn } }
      },
      {
        Sid      = "IamRoles"
        Effect   = "Allow"
        Action   = ["iam:DeleteRole", "iam:GetRole", "iam:TagRole", "iam:UntagRole", "iam:UpdateRole", "iam:UpdateRoleDescription", "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:UpdateAssumeRolePolicy", "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:ListInstanceProfilesForRole", "iam:PassRole"]
        Resource = [local.app_role_arn_pattern]
      },
    ],
    local.deny_statements,
  )

  # Rol de plan: minimo (NFR5.3). El plan de las solicitudes corre con `init -backend=false` contra
  # un estado VACIO: no refresca nada y solo necesita saber quien es. Las lecturas de Cognito
  # (DescribeIdentityProvider devuelve el client_secret) y de Lambda (GetFunction devuelve las
  # variables de entorno, con ALLOWED_EMAILS) exponen secretos, asi que no se permiten ni se
  # leen recursos. Las denegaciones explicitas hacen que una ampliacion futura no las abra por error.
  plan_statements = [
    {
      Sid      = "AllowStsIdentity"
      Effect   = "Allow"
      Action   = ["sts:GetCallerIdentity"]
      Resource = ["*"]
    },
    {
      Sid    = "DenySecretBearingReads"
      Effect = "Deny"
      Action = [
        "cognito-idp:DescribeIdentityProvider", "cognito-idp:GetIdentityProviderByIdentifier",
        "lambda:GetFunction", "lambda:GetFunctionConfiguration", "lambda:GetFunctionUrlConfig",
        "secretsmanager:*", "ssm:GetParameter*",
      ]
      Resource = ["*"]
    },
    {
      Sid      = "DenyStateRead"
      Effect   = "Deny"
      Action   = ["s3:GetObject", "s3:GetObjectVersion"]
      Resource = ["${local.state_bucket_arn}/*"]
    },
  ]
}

# ---------------------------------------------------------------------------
# Estado remoto de infra/ (NFR5.6): privado, versionado, cifrado y solo por TLS.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "state" {
  bucket        = var.state_bucket_name
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = ["s3:*"]
      Resource  = [local.state_bucket_arn, "${local.state_bucket_arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })

  depends_on = [aws_s3_bucket_public_access_block.state]
}

# ---------------------------------------------------------------------------
# Identidad federada de GitHub (NFR5.2): sin claves de larga duracion.
# ---------------------------------------------------------------------------

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://${local.oidc_host}"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_policy" "boundary" {
  name        = local.boundary_name
  description = "Limite de los roles que Terraform crea (NFR5.4): solo registros y el modelo; sin IAM."

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = local.boundary_statements
  })
}

# Techo del rol de aplicacion (distinto del limite de los roles creados).
resource "aws_iam_policy" "apply_boundary" {
  name        = local.apply_boundary_name
  description = "Techo del rol de aplicacion (NFR5.4): servicios de la aplicacion; el arranque denegado."

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = local.apply_boundary_statements
  })
}

resource "aws_iam_role" "plan" {
  name               = local.plan_role_name
  description        = "Plan de las solicitudes de integracion: solo sts:GetCallerIdentity, sin lecturas ni estado (NFR5.3)."
  assume_role_policy = local.oidc_trust["plan"]
}

resource "aws_iam_role_policy" "plan" {
  name = "plan-read-only"
  role = aws_iam_role.plan.id

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = local.plan_statements
  })
}

resource "aws_iam_role" "apply" {
  name                 = local.apply_role_name
  description          = "Aplicacion en main: solo los recursos de la aplicacion y con el limite de permisos (NFR5.4)."
  assume_role_policy   = local.oidc_trust["apply"]
  permissions_boundary = aws_iam_policy.apply_boundary.arn
}

resource "aws_iam_role_policy" "apply" {
  name = "apply-application"
  role = aws_iam_role.apply.id

  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = concat(local.apply_allow_statements, local.deny_statements)
  })
}
