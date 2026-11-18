# Paso 12 (arranque): confianza y permisos de los roles de plan y de aplicacion, limite de
# permisos y denegaciones (NFR5.2 a NFR5.4, NFR5.6). Las politicas se escriben con jsonencode y se
# decodifican aqui; los datos de cuenta se simulan con valores explicitos. Sin AWS.
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

override_resource {
  override_during = plan
  target          = aws_iam_openid_connect_provider.github
  values = {
    arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  }
}

override_resource {
  override_during = plan
  target          = aws_iam_policy.boundary
  values = {
    arn = "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-boundary"
  }
}

override_resource {
  override_during = plan
  target          = aws_iam_policy.apply_boundary
  values = {
    arn = "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-apply-boundary"
  }
}

# ---- Confianza (NFR5.2) ------------------------------------------------------------------

run "plan_role_trusts_only_pull_request_tokens_of_the_repository" {
  command = plan

  assert {
    condition = (
      jsondecode(aws_iam_role.plan.assume_role_policy).Statement[0].Effect == "Allow" &&
      jsondecode(aws_iam_role.plan.assume_role_policy).Statement[0].Action == "sts:AssumeRoleWithWebIdentity" &&
      jsondecode(aws_iam_role.plan.assume_role_policy).Statement[0].Principal == { Federated = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" } &&
      jsondecode(aws_iam_role.plan.assume_role_policy).Statement[0].Condition == {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:example-org/example-repo:pull_request"
        }
      }
    )
    error_message = "El rol de plan solo se asume con sub repo:<org>/<repo>:pull_request y aud sts.amazonaws.com."
  }
}

run "apply_role_trusts_only_the_main_branch_of_the_repository" {
  command = plan

  assert {
    condition = (
      jsondecode(aws_iam_role.apply.assume_role_policy).Statement[0].Action == "sts:AssumeRoleWithWebIdentity" &&
      jsondecode(aws_iam_role.apply.assume_role_policy).Statement[0].Principal == { Federated = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" } &&
      jsondecode(aws_iam_role.apply.assume_role_policy).Statement[0].Condition == {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:example-org/example-repo:ref:refs/heads/main"
        }
      }
    )
    error_message = "El rol de aplicacion solo se asume con sub repo:<org>/<repo>:ref:refs/heads/main y aud sts.amazonaws.com."
  }
}

run "trust_policies_have_one_statement_and_no_wildcards" {
  command = plan

  assert {
    condition = alltrue([
      for doc in [aws_iam_role.plan.assume_role_policy, aws_iam_role.apply.assume_role_policy] :
      length(jsondecode(doc).Statement) == 1 &&
      !strcontains(doc, "*") &&
      !strcontains(doc, "StringLike")
    ])
    error_message = "La confianza no admite comodines (*) ni StringLike."
  }
}

# ---- Rol de plan: solo lectura (NFR5.3) --------------------------------------------------

# ---- Rol de plan: minimo (NFR5.3) ---------------------------------------------------------
# El plan de las solicitudes corre con `init -backend=false` contra un estado VACIO: no refresca
# nada y no necesita leer recursos. Las lecturas de Cognito (client_secret de las federaciones) y de
# Lambda (variables de entorno, incluida ALLOWED_EMAILS) exponen secretos, asi que el rol solo puede
# preguntar quien es (sts:GetCallerIdentity).

run "plan_role_allows_exactly_sts_get_caller_identity" {
  command = plan

  assert {
    condition = (
      length([for s in jsondecode(aws_iam_role_policy.plan.policy).Statement : s if s.Effect == "Allow"]) == 1 &&
      anytrue([for s in jsondecode(aws_iam_role_policy.plan.policy).Statement :
        s.Effect == "Allow" && s.Action == ["sts:GetCallerIdentity"] && s.Resource == ["*"]
      ])
    )
    error_message = "El rol de plan solo permite sts:GetCallerIdentity."
  }
}

run "plan_role_has_no_service_actions_and_no_write_actions" {
  command = plan

  assert {
    condition = alltrue([
      for s in jsondecode(aws_iam_role_policy.plan.policy).Statement :
      s.Effect == "Deny" || alltrue([
        for a in s.Action :
        !anytrue([for svc in ["cognito-idp:", "lambda:", "iam:", "s3:", "apigateway:", "cloudfront:", "logs:", "cloudwatch:", "secretsmanager:", "ssm:"] : startswith(a, svc)])
      ])
    ])
    error_message = "El rol de plan no tiene acciones de Cognito, Lambda, IAM, S3, API Gateway ni de otros servicios."
  }
}

run "plan_role_explicitly_denies_secret_bearing_reads" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.plan.policy).Statement :
      s.Sid == "DenySecretBearingReads" && s.Effect == "Deny" && s.Resource == ["*"] &&
      toset(s.Action) == toset([
        "cognito-idp:DescribeIdentityProvider", "cognito-idp:GetIdentityProviderByIdentifier",
        "lambda:GetFunction", "lambda:GetFunctionConfiguration", "lambda:GetFunctionUrlConfig",
        "secretsmanager:*", "ssm:GetParameter*",
      ])
    ])
    error_message = "Denegacion explicita de las lecturas que devuelven secretos."
  }
}

run "plan_role_explicitly_denies_reading_the_state_bucket_objects" {
  command = plan

  assert {
    condition = (
      anytrue([
        for s in jsondecode(aws_iam_role_policy.plan.policy).Statement :
        s.Sid == "DenyStateRead" && s.Effect == "Deny" &&
        toset(s.Action) == toset(["s3:GetObject", "s3:GetObjectVersion"]) &&
        s.Resource == ["arn:aws:s3:::example-ba-agent-tfstate-123456789012/*"]
      ]) &&
      !strcontains(aws_iam_role_policy.plan.policy, "tflock") &&
      length(jsondecode(aws_iam_role_policy.plan.policy).Statement) == 3
    )
    error_message = "El rol de plan no lee el estado: denegacion explicita sobre los objetos del deposito."
  }
}

# El estado contiene los secretos de cliente de las federaciones: el rol de plan no lo lee. El plan
# de las solicitudes corre con `init -backend=false` y no necesita acceso al deposito de estado.
# ---- Estado remoto: ListBucket por prefijo (NFR5.6) --------------------------------------

run "apply_role_lists_the_state_bucket_only_with_the_prefix_condition" {
  command = plan

  assert {
    condition = alltrue([
      for doc in [aws_iam_role_policy.apply.policy] :
      anytrue([
        for s in jsondecode(doc).Statement :
        s.Sid == "StateListBucket" && s.Effect == "Allow" && s.Action == ["s3:ListBucket"] &&
        s.Resource == ["arn:aws:s3:::example-ba-agent-tfstate-123456789012"] &&
        s.Condition == {
          StringLikeIfExists = {
            "s3:prefix" = ["business-analyst-agent/", "business-analyst-agent/*", "env:/", "env:/*"]
          }
        }
      ])
    ])
    error_message = "s3:ListBucket con StringLikeIfExists sobre s3:prefix y la lista explicita de prefijos."
  }
}

run "roles_have_no_other_actions_on_the_state_bucket_itself" {
  command = plan

  assert {
    condition = alltrue([
      for doc in [aws_iam_role_policy.apply.policy] :
      alltrue([
        for s in jsondecode(doc).Statement :
        s.Effect == "Deny" || !contains(s.Resource, "arn:aws:s3:::example-ba-agent-tfstate-123456789012") || s.Action == ["s3:ListBucket"]
      ])
    ])
    error_message = "Sobre el deposito de estado solo se permite s3:ListBucket."
  }
}

run "apply_role_state_object_access_is_state_and_lock_only" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Sid == "StateObject" && s.Effect == "Allow" &&
      toset(s.Action) == toset(["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]) &&
      toset(s.Resource) == toset([
        "arn:aws:s3:::example-ba-agent-tfstate-123456789012/business-analyst-agent/terraform.tfstate",
        "arn:aws:s3:::example-ba-agent-tfstate-123456789012/business-analyst-agent/terraform.tfstate.tflock",
      ])
    ])
    error_message = "El rol de aplicacion lee, escribe y borra solo el estado y su .tflock."
  }
}

# ---- Rol de aplicacion: limite y acotaciones (NFR5.4) ------------------------------------

run "apply_role_has_its_own_permissions_boundary" {
  command = plan

  assert {
    condition     = aws_iam_role.apply.permissions_boundary == "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-apply-boundary"
    error_message = "El rol de aplicacion lleva el limite de permisos."
  }
}

run "apply_role_creates_roles_only_with_the_boundary_and_the_prefix" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Sid == "IamCreateRole" && s.Effect == "Allow" && s.Action == ["iam:CreateRole"] &&
      s.Resource == ["arn:aws:iam::123456789012:role/business-analyst-agent-*"] &&
      s.Condition == { StringEquals = { "iam:PermissionsBoundary" = "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-boundary" } }
    ])
    error_message = "iam:CreateRole solo con la condicion iam:PermissionsBoundary igual al limite y sobre el prefijo."
  }
}

run "apply_role_policy_actions_are_scoped_by_role_name_prefix" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Sid == "IamManageRoles" && s.Effect == "Allow" &&
      s.Resource == ["arn:aws:iam::123456789012:role/business-analyst-agent-*"] &&
      alltrue([for a in ["iam:AttachRolePolicy", "iam:PutRolePolicy", "iam:UpdateAssumeRolePolicy", "iam:DeleteRole", "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "iam:ListInstanceProfilesForRole"] : contains(s.Action, a)])
    ])
    error_message = "Las acciones de politica de rol estan acotadas al prefijo del nombre de rol."
  }
}

run "apply_role_pass_role_only_to_lambda_and_only_prefixed_roles" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Sid == "IamPassRole" && s.Action == ["iam:PassRole"] &&
      s.Resource == ["arn:aws:iam::123456789012:role/business-analyst-agent-*"] &&
      s.Condition == { StringEquals = { "iam:PassedToService" = "lambda.amazonaws.com" } }
    ])
    error_message = "iam:PassRole solo hacia Lambda y solo para roles con el prefijo."
  }
}

run "apply_role_has_no_unscoped_iam_allow_and_no_service_linked_roles" {
  command = plan

  assert {
    condition = alltrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Effect == "Deny" || (
        !contains(s.Action, "iam:*") &&
        !contains(s.Action, "iam:CreateServiceLinkedRole") &&
        !contains(s.Action, "apigateway:UpdateAccount") &&
        (!anytrue([for a in s.Action : startswith(a, "iam:")]) || !contains(s.Resource, "*"))
      )
    ])
    error_message = "Ninguna accion de IAM sin acotar, sin roles vinculados a servicios y sin la cuenta de la pasarela."
  }
}

run "apply_role_denies_changes_to_bootstrap_resources" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
      s.Sid == "DenyBootstrapIam" && s.Effect == "Deny" && s.Action == ["iam:*"] &&
      toset(s.Resource) == toset([
        "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-boundary",
        "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-apply-boundary",
        "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com",
        "arn:aws:iam::123456789012:role/pipeline-business-analyst-agent-plan",
        "arn:aws:iam::123456789012:role/pipeline-business-analyst-agent-apply",
      ])
    ])
    error_message = "Denegacion explicita sobre el limite, el proveedor OIDC y los dos roles de la canalizacion."
  }
}

run "apply_role_denies_state_bucket_administration_and_boundary_removal" {
  command = plan

  assert {
    condition = (
      anytrue([for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
        s.Sid == "DenyStateBucketAdmin" && s.Effect == "Deny" &&
        s.Resource == ["arn:aws:s3:::example-ba-agent-tfstate-123456789012"] &&
        alltrue([for a in ["s3:DeleteBucket", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy", "s3:PutBucketVersioning", "s3:PutEncryptionConfiguration", "s3:PutBucketPublicAccessBlock"] : contains(s.Action, a)])
      ]) &&
      anytrue([for s in jsondecode(aws_iam_role_policy.apply.policy).Statement :
        s.Sid == "DenyBoundaryRemoval" && s.Effect == "Deny" &&
        s.Action == ["iam:DeleteRolePermissionsBoundary"]
      ])
    )
    error_message = "Denegar administrar el deposito de estado y quitar o cambiar el limite de un rol."
  }
}

# ---- Limite de permisos (NFR5.4) ---------------------------------------------------------

# ---- Limites de permisos (NFR5.4) --------------------------------------------------------

# Una politica con el limite y permisos amplios no puede crear un rol sin limite: denegacion
# explicita de iam:CreateRole e iam:PutRolePermissionsBoundary si el limite pedido no es el esperado.
run "unbounded_role_creation_is_denied_in_both_boundaries_and_the_apply_policy" {
  command = plan

  assert {
    condition = alltrue([
      for doc in [aws_iam_policy.boundary.policy, aws_iam_policy.apply_boundary.policy, aws_iam_role_policy.apply.policy] :
      anytrue([
        for s in jsondecode(doc).Statement :
        s.Sid == "DenyUnboundedRoles" && s.Effect == "Deny" &&
        toset(s.Action) == toset(["iam:CreateRole", "iam:PutRolePermissionsBoundary"]) &&
        s.Resource == ["*"] &&
        s.Condition == { StringNotEquals = { "iam:PermissionsBoundary" = "arn:aws:iam::123456789012:policy/pipeline-business-analyst-agent-boundary" } }
      ])
    ])
    error_message = "Falta la denegacion de crear roles (o cambiar su limite) sin el limite esperado."
  }
}

run "no_policy_allows_create_role_without_the_boundary_condition" {
  command = plan

  assert {
    condition = alltrue([
      for doc in [aws_iam_policy.boundary.policy, aws_iam_policy.apply_boundary.policy, aws_iam_role_policy.apply.policy] :
      alltrue([
        for s in jsondecode(doc).Statement :
        s.Effect == "Deny" || !contains(s.Action, "iam:CreateRole") || try(s.Condition, null) != null
      ])
    ])
    error_message = "Ninguna politica puede permitir iam:CreateRole sin la condicion del limite."
  }
}

# El techo de los roles que Terraform crea (funcion): solo registros y el modelo; sin IAM.
run "created_role_boundary_allows_only_logs_and_the_model" {
  command = plan

  assert {
    condition = (
      alltrue([
        for s in jsondecode(aws_iam_policy.boundary.policy).Statement :
        s.Effect == "Deny" || alltrue([for a in s.Action : startswith(a, "logs:") || a == "bedrock:InvokeModel"])
      ]) &&
      anytrue([for s in jsondecode(aws_iam_policy.boundary.policy).Statement :
        s.Sid == "FunctionLogs" && s.Effect == "Allow" && toset(s.Action) == toset(["logs:CreateLogStream", "logs:PutLogEvents"])
      ]) &&
      anytrue([for s in jsondecode(aws_iam_policy.boundary.policy).Statement :
        s.Sid == "InvokeBedrockModel" && s.Effect == "Allow" && s.Action == ["bedrock:InvokeModel"]
      ])
    )
    error_message = "El limite de los roles creados no admite IAM, S3 ni otros servicios."
  }
}

# El techo del rol de aplicacion: solo los servicios de la aplicacion y el arranque denegado.
run "apply_boundary_allows_only_application_services_and_denies_bootstrap" {
  command = plan

  assert {
    condition = (
      anytrue([for s in jsondecode(aws_iam_policy.apply_boundary.policy).Statement :
        s.Sid == "DenyBootstrapIam" && s.Effect == "Deny" && s.Action == ["iam:*"]
      ]) &&
      alltrue([for s in jsondecode(aws_iam_policy.apply_boundary.policy).Statement :
        s.Effect == "Deny" || alltrue([for a in s.Action : anytrue([for svc in ["lambda:", "apigateway:", "s3:", "cloudfront:", "cognito-idp:", "logs:", "cloudwatch:", "iam:"] : startswith(a, svc)])])
      ]) &&
      !anytrue([for s in jsondecode(aws_iam_policy.apply_boundary.policy).Statement : contains(s.Action, "bedrock:InvokeModel")])
    )
    error_message = "El techo del rol de aplicacion: servicios de la aplicacion; sin invocar el modelo."
  }
}

# ---- Limites de tamano de IAM (limite administrado 6 144 caracteres; en linea 10 240) ----

run "policies_fit_the_iam_size_limits" {
  command = plan

  assert {
    condition = (
      length(replace(aws_iam_policy.boundary.policy, " ", "")) <= 6144 &&
      length(replace(aws_iam_policy.apply_boundary.policy, " ", "")) <= 6144 &&
      length(replace(aws_iam_role_policy.apply.policy, " ", "")) <= 10240 &&
      length(replace(aws_iam_role_policy.plan.policy, " ", "")) <= 10240
    )
    error_message = "Una politica supera el limite de tamano de IAM."
  }
}

run "bootstrap_role_names_do_not_match_the_application_prefix" {
  command = plan

  assert {
    condition = (
      !startswith(aws_iam_role.plan.name, "business-analyst-agent-") &&
      !startswith(aws_iam_role.apply.name, "business-analyst-agent-") &&
      !startswith(aws_iam_policy.boundary.name, "business-analyst-agent-") &&
      !startswith(aws_iam_policy.apply_boundary.name, "business-analyst-agent-")
    )
    error_message = "Los roles del arranque no caen bajo el prefijo que el rol de aplicacion puede administrar."
  }
}

# ---- Limites de tamano de IAM (un limite administrado admite 6 144 caracteres y las politicas
# en linea de un rol suman 10 240, sin contar espacios) ------------------------------------


# El limite solo deja invocar las familias que valida bedrock_model_id (anthropic.claude-* y
# amazon.titan-*, con o sin prefijo us. o global.); el modelo exacto lo fija la politica del rol.
run "created_role_boundary_limits_the_model_families" {
  command = plan

  assert {
    condition = anytrue([
      for s in jsondecode(aws_iam_policy.boundary.policy).Statement :
      s.Sid == "InvokeBedrockModel" && toset(s.Resource) == toset([
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*::foundation-model/amazon.titan-*",
        "arn:aws:bedrock:*:123456789012:inference-profile/anthropic.claude-*",
        "arn:aws:bedrock:*:123456789012:inference-profile/us.anthropic.claude-*",
        "arn:aws:bedrock:*:123456789012:inference-profile/global.anthropic.claude-*",
        "arn:aws:bedrock:*:123456789012:inference-profile/amazon.titan-*",
        "arn:aws:bedrock:*:123456789012:inference-profile/us.amazon.titan-*",
      ])
    ])
    error_message = "El limite de los roles creados solo admite las familias de modelos validadas."
  }
}

run "created_role_boundary_has_no_catch_all_model_resource" {
  command = plan

  assert {
    condition = alltrue([
      for s in jsondecode(aws_iam_policy.boundary.policy).Statement :
      s.Effect == "Deny" || s.Sid != "InvokeBedrockModel" ||
      !anytrue([for r in s.Resource : endswith(r, "/*") || r == "*"])
    ])
    error_message = "Ningun recurso de modelo puede ser un comodin general."
  }
}
