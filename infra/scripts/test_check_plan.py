"""Pruebas de check_plan.py con planes de ejemplo (terraform show -json reducido). NFR4.1, NFR5.1,
NFR5.3 y NFR8.2. Nunca se llama a AWS: los planes son diccionarios escritos aqui."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import check_plan

SENSITIVE = [
    "allowed_emails",
    "google_client_id",
    "google_client_secret",
    "microsoft_client_id",
    "microsoft_client_secret",
]


def change(address: str, actions: list[str], after: dict | None = None) -> dict:
    rtype, name = address.split(".")
    return {
        "address": address,
        "mode": "managed",
        "type": rtype,
        "name": name,
        "change": {"actions": actions, "after": after or {}},
    }


def clean_plan() -> dict:
    return {
        "format_version": "1.2",
        "variables": {"allowed_emails": {"value": "dummy@example.com"}},
        "configuration": {
            "root_module": {
                "variables": {name: {"sensitive": True} for name in SENSITIVE},
                "resources": [
                    {
                        "address": "data.archive_file.story_service",
                        "mode": "data",
                        "type": "archive_file",
                    },
                    {
                        "address": "aws_lambda_function.story",
                        "mode": "managed",
                        "type": "aws_lambda_function",
                    },
                ],
                "module_calls": {},
            }
        },
        "resource_changes": [
            change("aws_lambda_function.story", ["create"]),
            change("aws_api_gateway_rest_api.api", ["create"]),
            change("aws_api_gateway_resource.session", ["create"]),
            change("aws_cloudwatch_log_group.story", ["create"]),
            change("aws_cloudwatch_log_metric_filter.requests_total", ["create"]),
            change("aws_cloudfront_distribution.web", ["create"]),
            change("aws_cloudfront_response_headers_policy.web", ["create"]),
            change("aws_cognito_user_pool.main", ["create"]),
            change("aws_cognito_identity_provider.google", ["create"]),
            change(
                "aws_s3_bucket.web", ["create"], {"bucket_prefix": "business-analyst-agent-web-"}
            ),
            change("aws_s3_bucket_policy.web", ["create"]),
            change(
                "aws_iam_role.story",
                ["create"],
                {"name": "business-analyst-agent-story-service-exec"},
            ),
            change("aws_iam_role_policy.story", ["create"]),
        ],
    }


def violations_for(mutate) -> list[str]:
    plan = copy.deepcopy(clean_plan())
    mutate(plan)
    return check_plan.check_plan(plan)


def test_clean_plan_is_accepted() -> None:
    assert check_plan.check_plan(clean_plan()) == []


def test_disallowed_resource_type_is_rejected() -> None:
    result = violations_for(
        lambda p: p["resource_changes"].append(change("aws_dynamodb_table.data", ["create"]))
    )
    assert any("aws_dynamodb_table" in line for line in result)


@pytest.mark.parametrize(
    "rtype", ["aws_db_instance", "aws_rds_cluster", "aws_iam_user", "terraform_data"]
)
def test_other_stores_and_identities_are_rejected(rtype: str) -> None:
    result = violations_for(
        lambda p: p["resource_changes"].append(change(f"{rtype}.x", ["create"]))
    )
    assert any(rtype in line for line in result)


def test_additional_bucket_is_rejected() -> None:
    result = violations_for(
        lambda p: p["resource_changes"].append(
            change("aws_s3_bucket.logs", ["create"], {"bucket": "data"})
        )
    )
    assert any("aws_s3_bucket.logs" in line for line in result)


def test_web_bucket_with_foreign_prefix_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_s3_bucket.web":
                item["change"]["after"] = {"bucket_prefix": "otra-cosa-"}

    assert any("aws_s3_bucket.web" in line for line in violations_for(mutate))


@pytest.mark.parametrize(
    ("address", "actions"),
    [
        ("aws_cognito_user_pool.main", ["delete"]),
        ("aws_cloudfront_distribution.web", ["delete", "create"]),
        ("aws_lambda_function.story", ["create", "delete"]),
        ("aws_s3_bucket.web", ["delete"]),
    ],
)
def test_delete_or_replace_of_protected_type_is_rejected(address: str, actions: list[str]) -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == address:
                item["change"]["actions"] = actions

    result = violations_for(mutate)
    assert any(address in line and "protegido" in line for line in result)


def test_update_and_noop_of_protected_type_are_allowed() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_cognito_user_pool.main":
                item["change"]["actions"] = ["update"]
            if item["address"] == "aws_lambda_function.story":
                item["change"]["actions"] = ["no-op"]

    assert violations_for(mutate) == []


def test_delete_of_unprotected_type_is_allowed() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_api_gateway_resource.session":
                item["change"]["actions"] = ["delete"]

    assert violations_for(mutate) == []


def test_variable_without_sensitive_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        plan["configuration"]["root_module"]["variables"]["google_client_secret"] = {}

    result = violations_for(mutate)
    assert any("google_client_secret" in line for line in result)


def test_missing_sensitive_variable_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        del plan["configuration"]["root_module"]["variables"]["allowed_emails"]

    assert any("allowed_emails" in line for line in violations_for(mutate))


def test_external_data_source_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        plan["configuration"]["root_module"]["resources"].append(
            {"address": "data.external.x", "mode": "data", "type": "external"}
        )

    assert any("external" in line for line in violations_for(mutate))


def test_external_data_source_in_resource_changes_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        plan["resource_changes"].append(
            {
                "address": "data.external.y",
                "mode": "data",
                "type": "external",
                "change": {"actions": ["read"]},
            }
        )

    assert any("data.external.y" in line for line in violations_for(mutate))


@pytest.mark.parametrize("kind", ["local-exec", "remote-exec"])
def test_exec_provisioners_are_rejected(kind: str) -> None:
    def mutate(plan: dict) -> None:
        plan["configuration"]["root_module"]["resources"][1]["provisioners"] = [{"type": kind}]

    assert any(kind in line for line in violations_for(mutate))


def test_provisioner_inside_child_module_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        plan["configuration"]["root_module"]["module_calls"] = {
            "child": {
                "module": {
                    "resources": [
                        {
                            "address": "null_resource.a",
                            "type": "null_resource",
                            "provisioners": [{"type": "local-exec"}],
                        }
                    ]
                }
            }
        }

    assert any("local-exec" in line for line in violations_for(mutate))


def test_iam_role_without_application_prefix_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_iam_role.story":
                item["change"]["after"] = {"name": "AdminRole"}

    assert any("aws_iam_role.story" in line for line in violations_for(mutate))


@pytest.mark.parametrize(
    "rtype",
    [
        "aws_s3_bucket_logging",
        "aws_cloudfront_realtime_log_config",
        "aws_bedrock_model_invocation_logging_configuration",
    ],
)
def test_access_and_invocation_logging_resources_are_rejected(rtype: str) -> None:
    """NFR4.2: sin registro de acceso ni de invocaciones del modelo."""
    result = violations_for(
        lambda p: p["resource_changes"].append(change(f"{rtype}.x", ["create"]))
    )
    assert any(rtype in line for line in result)


def test_distribution_with_access_logging_is_rejected() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_cloudfront_distribution.web":
                item["change"]["after"] = {"logging_config": [{"bucket": "x.s3.amazonaws.com"}]}

    assert any(
        "aws_cloudfront_distribution.web" in line and "registro" in line
        for line in violations_for(mutate)
    )


def test_distribution_with_empty_logging_config_is_accepted() -> None:
    def mutate(plan: dict) -> None:
        for item in plan["resource_changes"]:
            if item["address"] == "aws_cloudfront_distribution.web":
                item["change"]["after"] = {"logging_config": []}

    assert violations_for(mutate) == []


def test_placeholder_values_do_not_confuse_the_check() -> None:
    """Valores ficticios con palabras como external o local-exec no son estructura."""

    def mutate(plan: dict) -> None:
        plan["variables"]["google_client_secret"] = {"value": "external local-exec data.external"}
        plan["resource_changes"][0]["change"]["after"] = {
            "description": "external local-exec aws_dynamodb_table"
        }

    assert violations_for(mutate) == []


# ---- CLI --------------------------------------------------------------------------------


def test_main_returns_zero_for_clean_plan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(clean_plan()), encoding="utf-8")
    assert check_plan.main([str(path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_returns_one_and_never_prints_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    plan = clean_plan()
    plan["variables"]["google_client_secret"] = {"value": "super-secret-value-123"}
    plan["configuration"]["root_module"]["variables"]["google_client_secret"] = {}
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    assert check_plan.main([str(path)]) == 1
    out = capsys.readouterr()
    assert "super-secret-value-123" not in out.out + out.err
    assert "google_client_secret" in out.out + out.err


def test_main_returns_two_for_missing_file(tmp_path: Path) -> None:
    assert check_plan.main([str(tmp_path / "no-existe.json")]) == 2


def test_main_returns_two_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    path.write_text("{no es json", encoding="utf-8")
    assert check_plan.main([str(path)]) == 2


def test_main_returns_two_without_arguments() -> None:
    assert check_plan.main([]) == 2


# ---- Endurecimiento (revision adversarial) ------------------------------------------------


def with_change(item: dict) -> list[str]:
    return violations_for(lambda p: p["resource_changes"].append(item))


def test_attachment_of_an_aws_managed_policy_is_rejected() -> None:
    item = change(
        "aws_iam_role_policy_attachment.admin",
        ["create"],
        {"policy_arn": "arn:aws:iam::aws:policy/AdministratorAccess"},
    )
    assert any("aws_iam_role_policy_attachment.admin" in line for line in with_change(item))


def test_attachment_of_an_account_policy_is_accepted() -> None:
    item = change(
        "aws_iam_role_policy_attachment.own",
        ["create"],
        {"policy_arn": "arn:aws:iam::123456789012:policy/business-analyst-agent-x"},
    )
    assert with_change(item) == []


def test_attachment_with_unknown_policy_arn_is_accepted() -> None:
    item = change("aws_iam_role_policy_attachment.own", ["create"], {})
    assert with_change(item) == []


def test_lambda_function_url_is_rejected() -> None:
    result = with_change(change("aws_lambda_function_url.open", ["create"]))
    assert any("aws_lambda_function_url" in line for line in result)


def test_lambda_permission_for_any_principal_is_rejected() -> None:
    item = change("aws_lambda_permission.any", ["create"], {"principal": "*"})
    assert any("aws_lambda_permission.any" in line for line in with_change(item))


def test_lambda_permission_for_api_gateway_is_accepted() -> None:
    item = change(
        "aws_lambda_permission.apigw", ["create"], {"principal": "apigateway.amazonaws.com"}
    )
    assert with_change(item) == []


def test_pure_delete_of_a_prefixed_role_reads_the_name_from_before() -> None:
    item = change("aws_iam_role.old", ["delete"])
    item["change"]["before"] = {"name": "business-analyst-agent-old-exec"}
    item["change"]["after"] = None
    assert with_change(item) == []


def test_pure_delete_of_a_foreign_role_is_still_reported() -> None:
    item = change("aws_iam_role.old", ["delete"])
    item["change"]["before"] = {"name": "AdminRole"}
    item["change"]["after"] = None
    assert any("aws_iam_role.old" in line for line in with_change(item))


def test_pure_delete_of_the_web_bucket_reads_before() -> None:
    def mutate(plan: dict) -> None:
        for entry in plan["resource_changes"]:
            if entry["address"] == "aws_s3_bucket.web":
                entry["change"]["actions"] = ["delete"]
                entry["change"]["before"] = {"bucket_prefix": "business-analyst-agent-web-"}
                entry["change"]["after"] = None

    result = violations_for(mutate)
    assert all("deposito de S3 no permitido" not in line for line in result)
    assert any("protegido" in line for line in result)
