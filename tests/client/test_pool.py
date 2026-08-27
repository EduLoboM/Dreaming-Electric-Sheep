import ssl

import pytest

from dreaming_electric_sheep.client.connection import (
    INSECURE_SSLCONTEXT,
    SECURE_SSLCONTEXT,
)
from dreaming_electric_sheep.client.pool import ConnectionPool, get_ssl_context
from dreaming_electric_sheep.exceptions import InvalidArgument
from dreaming_electric_sheep.utils.aio import get_running_loop

example_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
example_context.check_hostname = False


@pytest.mark.parametrize(
    "scheme,ssl_option,expected_result",
    [
        (b"https", False, INSECURE_SSLCONTEXT),
        (b"https", True, SECURE_SSLCONTEXT),
        (b"https", None, SECURE_SSLCONTEXT),
        (b"https", example_context, example_context),
    ],
)
def test_get_ssl_context(scheme, ssl_option, expected_result):
    assert get_ssl_context(scheme, ssl_option) is expected_result


def test_get_ssl_context_for_http():
    assert get_ssl_context(b"http", True) is None
    assert get_ssl_context(b"http", SECURE_SSLCONTEXT) is None


def test_get_ssl_context_raises_for_invalid_argument():
    with pytest.raises(InvalidArgument):
        get_ssl_context(b"https", 1)  # type: ignore

    with pytest.raises(InvalidArgument):
        get_ssl_context(b"https", {})  # type: ignore
