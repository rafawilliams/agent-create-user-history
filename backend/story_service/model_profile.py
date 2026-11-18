"""Perfil de modelo: lista cerrada de identificadores por proveedor (BR2.1, BR2.2, NFR5.3)."""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_REGION = "us-east-1"

# Patron exacto por proveedor (security-design.md). Cualquier otro valor se rechaza.
_REST = r"[A-Za-z0-9][A-Za-z0-9._:-]*"
_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic": re.compile(rf"(us\.|global\.)?anthropic\.claude-{_REST}"),
    "amazon": re.compile(rf"(us\.)?amazon\.titan-{_REST}"),
}


class InvalidModelIdError(ValueError):
    """El identificador del modelo no es de un proveedor soportado (error de configuración)."""


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    provider: str
    region: str

    @classmethod
    def from_model_id(cls, model_id: str, region: str = DEFAULT_REGION) -> ModelProfile:
        """Valida el identificador y deduce el proveedor, antes de cualquier llamada a AWS."""
        if not isinstance(region, str) or not region.strip():
            raise ValueError("El campo obligatorio 'region' no puede estar vacío")
        if isinstance(model_id, str):
            for provider, pattern in _PATTERNS.items():
                if pattern.fullmatch(model_id):
                    return cls(model_id=model_id, provider=provider, region=region)
        raise InvalidModelIdError(
            f"Identificador de modelo no soportado: {model_id!r}. "
            "Se admite anthropic.claude-* (con prefijo us. o global.) y amazon.titan-* "
            "(con prefijo us.)."
        )
