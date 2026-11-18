"""Pruebas de las claves publicas: descarga acotada, copia, cerrojo y limite por minuto (BR4.7)."""

import io
import json
import ssl
import threading
import urllib.error
import urllib.request

import pytest

from story_service.jwks_store import (
    FETCH_TIMEOUT_SECONDS,
    MAX_RESPONSE_BYTES,
    HttpsJwksFetcher,
    JwksStore,
    KeyNotFoundError,
    KeysUnavailableError,
)
from tests.auth_helpers import (
    CONFIG,
    KID,
    OTHER_PRIVATE_KEY,
    PRIVATE_KEY,
    REGION,
    FakeClock,
    FakeKeyServer,
    jwk_for,
    jwks_bytes,
    make_store,
)


def _numbers(key):
    return key.public_numbers() if hasattr(key, "public_numbers") else None


def test_downloads_from_the_address_built_from_the_configuration_and_returns_the_key():
    server = FakeKeyServer()
    store = make_store(server)

    key = store.get_key(KID)

    assert server.urls == [CONFIG.jwks_url]
    assert _numbers(key) == _numbers(PRIVATE_KEY.public_key())


def test_a_copy_younger_than_one_hour_serves_without_any_network_call():
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)

    clock.advance(3599)
    for _ in range(20):
        store.get_key(KID)

    assert server.calls == 1


def test_unknown_kid_after_a_successful_refresh_by_this_request_is_not_found():
    server = FakeKeyServer()
    store = make_store(server)

    with pytest.raises(KeyNotFoundError):
        store.get_key("kid-desconocido")

    assert server.calls == 1


def test_unknown_kid_with_the_download_down_is_keys_unavailable_and_known_kid_still_serves():
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)
    clock.advance(61)
    server.error = TimeoutError("servidor caído")

    with pytest.raises(KeysUnavailableError):
        store.get_key("otro-kid")

    assert _numbers(store.get_key(KID)) == _numbers(PRIVATE_KEY.public_key())


def test_a_copy_older_than_one_hour_is_never_used():
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)
    clock.advance(3601)
    server.error = OSError("sin red")

    with pytest.raises(KeysUnavailableError):
        store.get_key(KID)

    server.error = None
    with pytest.raises(KeysUnavailableError):  # dentro del minuto no hay otro intento
        store.get_key(KID)
    clock.advance(61)
    assert store.get_key(KID) is not None  # tras el minuto vuelve a descargar


def test_an_expired_copy_is_refreshed_and_the_new_keys_replace_the_old_ones():
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)
    clock.advance(3601)
    server.body = jwks_bytes(jwk_for(OTHER_PRIVATE_KEY, kid="kid-nuevo"))

    key = store.get_key("kid-nuevo")

    assert _numbers(key) == _numbers(OTHER_PRIVATE_KEY.public_key())
    assert server.calls == 2
    clock.advance(61)
    with pytest.raises(KeyNotFoundError):  # la copia nueva ya no tiene el kid viejo
        store.get_key(KID)


def test_one_download_per_minute_counting_failures_with_100_unknown_kids():
    server, clock = FakeKeyServer(), FakeClock()
    server.error = ConnectionError("servidor caído")
    store = make_store(server, clock)

    for number in range(100):
        with pytest.raises(KeysUnavailableError):
            store.get_key(f"kid-{number}")
    assert server.calls == 1

    clock.advance(59)
    with pytest.raises(KeysUnavailableError):
        store.get_key("kid-x")
    assert server.calls == 1

    clock.advance(2)
    with pytest.raises(KeysUnavailableError):
        store.get_key("kid-y")
    assert server.calls == 2


def test_a_request_that_does_not_get_the_lock_fails_closed_immediately_without_waiting():
    server = FakeKeyServer()
    entered, release = threading.Event(), threading.Event()

    def block() -> None:
        entered.set()
        release.wait(5)

    server.on_fetch = block
    store = make_store(server)
    first_result: list[object] = []
    worker = threading.Thread(target=lambda: first_result.append(store.get_key(KID)))
    worker.start()
    assert entered.wait(5)

    try:
        with pytest.raises(KeysUnavailableError):
            store.get_key("kid-otro")  # vuelve de inmediato: no espera la descarga en curso
        assert server.calls == 1
    finally:
        release.set()
        worker.join(5)

    assert first_result and first_result[0] is not None
    assert store.get_key(KID) is not None  # la siguiente solicitud ya usa la copia renovada


@pytest.mark.parametrize(
    "body",
    [
        b"no es json",
        b"[]",
        b'{"keys": "no es lista"}',
        b'{"keys": []}',
        b'{"keys": ["texto"]}',
        jwks_bytes(jwk_for(PRIVATE_KEY, alg="RS512")),
        jwks_bytes(jwk_for(PRIVATE_KEY, kty="EC")),
        jwks_bytes({"kty": "RSA", "alg": "RS256", "kid": KID, "n": "!!", "e": "AQAB"}),
        jwks_bytes({k: v for k, v in jwk_for(PRIVATE_KEY).items() if k != "kid"}),
    ],
)
def test_a_malformed_key_set_is_keys_unavailable_and_leaves_the_previous_copy_untouched(body):
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)
    clock.advance(61)
    server.body = body

    with pytest.raises(KeysUnavailableError):
        store.get_key("kid-desconocido")

    assert _numbers(store.get_key(KID)) == _numbers(PRIVATE_KEY.public_key())
    assert server.calls == 2


def test_twenty_concurrent_verifications_are_served_by_the_copy_during_a_refresh():
    server, clock = FakeKeyServer(), FakeClock()
    store = make_store(server, clock)
    store.get_key(KID)
    clock.advance(61)
    entered, release = threading.Event(), threading.Event()
    server.on_fetch = lambda: (entered.set(), release.wait(5))
    refresher = threading.Thread(target=lambda: _swallow(store, "kid-nuevo"))
    refresher.start()
    assert entered.wait(5)

    results: list[object] = []
    threads = [
        threading.Thread(target=lambda: results.append(store.get_key(KID))) for _ in range(20)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    release.set()
    refresher.join(5)

    assert len(results) == 20
    assert all(_numbers(key) == _numbers(PRIVATE_KEY.public_key()) for key in results)


def _swallow(store: JwksStore, kid: str) -> None:
    try:
        store.get_key(kid)
    except (KeyNotFoundError, KeysUnavailableError):
        pass


# --- Descarga HTTP acotada (HttpsJwksFetcher) ---


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Opener:
    def __init__(self, payload: bytes | Exception) -> None:
        self.payload = payload
        self.requests: list[tuple[str, float]] = []

    def open(self, request, timeout):
        self.requests.append((request.full_url, timeout))
        if isinstance(self.payload, Exception):
            raise self.payload
        return _Response(self.payload)


def test_fetcher_reads_the_body_with_a_3_second_timeout_and_a_single_attempt():
    opener = _Opener(b'{"keys": []}')

    body = HttpsJwksFetcher(opener=opener)(CONFIG.jwks_url)

    assert body == b'{"keys": []}'
    assert opener.requests == [(CONFIG.jwks_url, FETCH_TIMEOUT_SECONDS)]
    assert FETCH_TIMEOUT_SECONDS == 3


def test_fetcher_accepts_a_body_of_exactly_64_kb_and_rejects_one_byte_more():
    assert MAX_RESPONSE_BYTES == 64 * 1024
    exact = b"x" * MAX_RESPONSE_BYTES

    assert HttpsJwksFetcher(opener=_Opener(exact))(CONFIG.jwks_url) == exact
    with pytest.raises(ValueError, match="64"):
        HttpsJwksFetcher(opener=_Opener(exact + b"x"))(CONFIG.jwks_url)


@pytest.mark.parametrize("url", ["http://cognito-idp.us-east-1.amazonaws.com/x", "ftp://a/b", ""])
def test_fetcher_refuses_anything_that_is_not_https(url):
    opener = _Opener(b"{}")

    with pytest.raises(ValueError, match="HTTPS"):
        HttpsJwksFetcher(opener=opener)(url)

    assert opener.requests == []


def test_fetcher_does_not_retry_a_failed_download():
    opener = _Opener(urllib.error.URLError("sin red"))

    with pytest.raises(urllib.error.URLError):
        HttpsJwksFetcher(opener=opener)(CONFIG.jwks_url)

    assert len(opener.requests) == 1


def test_default_opener_validates_certificates_and_refuses_a_redirect_to_another_host():
    opener = HttpsJwksFetcher().opener
    https = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPSHandler)]
    redirect = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
    request = urllib.request.Request(CONFIG.jwks_url)

    assert https and https[0]._context.verify_mode == ssl.CERT_REQUIRED
    assert https[0]._context.check_hostname is True
    assert len(redirect) == 1
    same_host = f"https://cognito-idp.{REGION}.amazonaws.com/otra-ruta"
    followed = redirect[0].redirect_request(request, io.BytesIO(b""), 302, "Found", {}, same_host)
    assert followed is not None and followed.full_url == same_host
    with pytest.raises(urllib.error.HTTPError):
        redirect[0].redirect_request(request, None, 302, "Found", {}, "https://atacante.example/k")
    with pytest.raises(urllib.error.HTTPError):
        redirect[0].redirect_request(
            request, None, 302, "Found", {}, "http://cognito-idp.us-east-1.amazonaws.com/k"
        )


# --- Plazo total de la descarga (NFR1.2): cuenta desde el inicio de la conexion ---


class _DripResponse:
    """Respuesta que entrega trozos pequeños y hace avanzar el reloj en cada lectura."""

    def __init__(self, clock, payload: bytes, seconds_per_read: float) -> None:
        self._clock, self._data, self._step = clock, io.BytesIO(payload), seconds_per_read
        self.reads = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        self.reads += 1
        self._clock.advance(self._step)
        return self._data.read(min(size, 100) if size and size > 0 else 100)


class _SlowOpener:
    def __init__(self, clock, payload: bytes, connect_seconds=0.0, seconds_per_read=0.0) -> None:
        self.clock, self.payload = clock, payload
        self.connect_seconds, self.seconds_per_read = connect_seconds, seconds_per_read
        self.response = None

    def open(self, request, timeout):
        self.clock.advance(self.connect_seconds)
        self.response = _DripResponse(self.clock, self.payload, self.seconds_per_read)
        return self.response


def test_a_slow_drip_download_is_abandoned_once_3_seconds_have_passed_in_total():
    clock = FakeClock(0.0)
    opener = _SlowOpener(clock, b"x" * 60000, seconds_per_read=0.5)

    with pytest.raises(TimeoutError, match="3"):
        HttpsJwksFetcher(opener=opener, clock=clock)(CONFIG.jwks_url)

    assert opener.response.reads <= 7  # corta al pasar 3 s; no lee hasta el tope de 64 KB


def test_time_spent_connecting_counts_towards_the_total_deadline():
    clock = FakeClock(0.0)
    opener = _SlowOpener(clock, b'{"keys": []}', connect_seconds=3.5)

    with pytest.raises(TimeoutError):
        HttpsJwksFetcher(opener=opener, clock=clock)(CONFIG.jwks_url)

    assert opener.response is None or opener.response.reads == 0


def test_a_complete_response_that_arrives_within_3_seconds_still_succeeds():
    clock = FakeClock(0.0)
    payload = b"y" * 1000  # 10 lecturas de 100 bytes de 0,2 s = 2 s
    opener = _SlowOpener(clock, payload, connect_seconds=0.5, seconds_per_read=0.2)

    assert HttpsJwksFetcher(opener=opener, clock=clock)(CONFIG.jwks_url) == payload


def test_chunked_reads_keep_the_64_kb_cap_exactly():
    clock = FakeClock(0.0)
    exact = b"z" * MAX_RESPONSE_BYTES

    assert HttpsJwksFetcher(opener=_SlowOpener(clock, exact), clock=clock)(CONFIG.jwks_url) == exact
    with pytest.raises(ValueError, match="64"):
        HttpsJwksFetcher(opener=_SlowOpener(clock, exact + b"z"), clock=clock)(CONFIG.jwks_url)


def test_a_total_deadline_failure_is_keys_unavailable_leaves_the_copy_and_frees_the_lock():
    clock = FakeClock(0.0)
    good = FakeKeyServer()
    store_clock = FakeClock()
    store = JwksStore(CONFIG.jwks_url, fetcher=good, clock=store_clock)
    store.get_key(KID)
    store_clock.advance(61)
    slow = HttpsJwksFetcher(opener=_SlowOpener(clock, b"x" * 5000, seconds_per_read=1), clock=clock)
    store._fetcher = slow

    with pytest.raises(KeysUnavailableError):
        store.get_key("kid-desconocido")

    assert store._lock.acquire(blocking=False)  # el cerrojo quedó libre
    store._lock.release()
    assert store.get_key(KID) is not None  # la copia anterior sigue intacta


def test_the_store_treats_any_fetcher_error_as_keys_unavailable():
    for error in (
        ValueError("grande"),
        urllib.error.URLError("x"),
        json.JSONDecodeError("m", "d", 0),
    ):
        server = FakeKeyServer()
        server.error = error

        with pytest.raises(KeysUnavailableError):
            make_store(server).get_key(KID)
