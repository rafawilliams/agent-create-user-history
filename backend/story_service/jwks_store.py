"""Claves publicas del grupo de usuarios: descarga acotada, copia en memoria y cerrojo (BR4.7).

Reglas (security-design.md):
- La direccion la fija quien construye el almacen a partir de la configuracion; nunca viene
  del token.
- Solo HTTPS con certificado validado, sin redirecciones a otro servidor, tope de 64 KB,
  3 segundos de espera y cero reintentos.
- Una copia por instancia, que sirve mientras tenga menos de 1 hora y contiene solo claves
  publicas. Una descarga a la vez y a lo sumo una por minuto contando los fallos; quien no
  obtiene el cerrojo no espera: falla cerrado.
"""

from __future__ import annotations

import json
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from jwt.algorithms import RSAAlgorithm

KEY_COPY_MAX_AGE_SECONDS = 3600.0
MIN_REFRESH_INTERVAL_SECONDS = 60.0
MAX_RESPONSE_BYTES = 64 * 1024
FETCH_TIMEOUT_SECONDS = 3
_CHUNK_BYTES = 4096

Fetcher = Callable[[str], bytes]


class KeyNotFoundError(Exception):
    """Esta solicitud descargó las claves con éxito y el kid sigue sin estar (bad_signature)."""


class KeysUnavailableError(Exception):
    """No hay copia vigente con el kid y esta solicitud no pudo renovarla (keys_unavailable)."""


class _SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Solo sigue una redireccion al mismo servidor y por HTTPS; cualquier otra falla."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        origin, target = urllib.parse.urlsplit(req.full_url), urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or target.hostname != origin.hostname:
            raise urllib.error.HTTPError(
                req.full_url, code, "redirección no permitida", headers, fp
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HttpsJwksFetcher:
    """Descarga acotada con la biblioteca estándar; el abridor se puede reemplazar en pruebas."""

    def __init__(
        self, opener: Any | None = None, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.opener = opener or self._build_opener()
        self._clock = clock

    @staticmethod
    def _build_opener() -> urllib.request.OpenerDirector:
        context = ssl.create_default_context()  # valida certificado y nombre del servidor
        return urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context), _SameHostRedirectHandler()
        )

    def __call__(self, url: str) -> bytes:
        if urllib.parse.urlsplit(url).scheme != "https":
            raise ValueError("Las claves públicas solo se descargan por HTTPS")
        started = self._clock()  # el plazo total cuenta desde el inicio de la conexión
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with self.opener.open(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            self._check_deadline(started)
            chunks: list[bytes] = []
            total = 0
            while total <= MAX_RESPONSE_BYTES:
                chunk = response.read(min(_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - total))
                self._check_deadline(started)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError("La respuesta de claves supera el tope de 64 KB")
        return b"".join(chunks)

    def _check_deadline(self, started: float) -> None:
        """El timeout de urllib es por operación de socket; este es el plazo total de 3 s."""
        if self._clock() - started > FETCH_TIMEOUT_SECONDS:
            raise TimeoutError("La descarga de claves superó el plazo total de 3 segundos")


@dataclass(frozen=True)
class _Snapshot:
    """Copia inmutable: se reemplaza entera, nunca se modifica (reemplazo atómico)."""

    keys: Mapping[str, Any]
    fetched_at: float


def _parse_key_set(raw: bytes) -> dict[str, Any]:
    """Conjunto válido de claves RSA para RS256, o ValueError (la copia anterior no se toca)."""
    data = json.loads(raw)
    entries = data.get("keys") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("El conjunto de claves no es válido")
    keys: dict[str, Any] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kty") != "RSA":
            raise ValueError("El conjunto de claves trae una clave que no es RSA")
        if entry.get("alg", "RS256") != "RS256":
            raise ValueError("El conjunto de claves trae un algoritmo distinto de RS256")
        kid = entry.get("kid")
        if not isinstance(kid, str) or not kid:
            raise ValueError("El conjunto de claves trae una clave sin kid")
        keys[kid] = RSAAlgorithm.from_jwk(json.dumps(entry))
    return keys


class JwksStore:
    def __init__(
        self,
        url: str,
        fetcher: Fetcher | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._url = url
        self._fetcher = fetcher or HttpsJwksFetcher()
        self._clock = clock
        self._snapshot: _Snapshot | None = None
        self._lock = threading.Lock()  # cerrojo de intento único
        self._last_attempt: float | None = None

    def get_key(self, kid: str) -> Any:
        """Regla única del kid (security-design.md, paso 4)."""
        snapshot = self._snapshot
        if (
            snapshot is not None
            and self._clock() - snapshot.fetched_at < KEY_COPY_MAX_AGE_SECONDS
            and kid in snapshot.keys
        ):
            return snapshot.keys[kid]
        if not self._refresh():
            raise KeysUnavailableError("No se pudieron obtener las claves públicas")
        refreshed = self._snapshot
        if refreshed is None or kid not in refreshed.keys:
            raise KeyNotFoundError("El kid no está en el conjunto de claves")
        return refreshed.keys[kid]

    def _refresh(self) -> bool:
        """True solo si ESTA solicitud descargó y guardó un conjunto válido."""
        if not self._lock.acquire(blocking=False):
            return False  # otra descarga en curso: no espera ni reutiliza su resultado
        try:
            now = self._clock()
            if (
                self._last_attempt is not None
                and now - self._last_attempt < MIN_REFRESH_INTERVAL_SECONDS
            ):
                return False
            self._last_attempt = now  # un intento fallido también cuenta
            try:
                keys = _parse_key_set(self._fetcher(self._url))
            except Exception:  # red, tiempo, tamaño, formato: la copia anterior queda igual
                return False
            self._snapshot = _Snapshot(MappingProxyType(keys), now)
            return True
        finally:
            self._lock.release()
