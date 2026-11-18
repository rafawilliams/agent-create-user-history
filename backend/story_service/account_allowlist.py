"""Lista de correos permitidos, leida del entorno en cada solicitud (BR4.3, NFR5.3, NFR5.6).

La lista no es un secreto, pero tampoco se guarda ni se registra: se lee, se normaliza a
minusculas y se compara de forma exacta (sin normalizar puntos ni alias).
"""

from __future__ import annotations

from collections.abc import Mapping

from story_service.auth_config import parse_allowed_emails

ALLOWED_EMAILS_VARIABLE = "ALLOWED_EMAILS"


def is_verified_email(value: object) -> bool:
    """Solo el booleano verdadero cuenta: "true", 1 o la ausencia no verifican el correo."""
    return value is True


def email_in(allowed: frozenset[str], email: object) -> bool:
    """Comparación exacta sobre el texto en minúsculas; sin normalizar puntos ni alias."""
    return isinstance(email, str) and email.strip().lower() in allowed


class AccountAllowlist:
    def __init__(self, env: Mapping[str, str]) -> None:
        self._env = env  # se conserva la referencia: cada solicitud lee el valor actual

    def emails(self) -> frozenset[str]:
        """La lista vigente. Más de 50 o una entrada rota: ValueError (error de configuración)."""
        return parse_allowed_emails(self._env.get(ALLOWED_EMAILS_VARIABLE))

    def is_allowed(self, email: object) -> bool:
        return email_in(self.emails(), email)
