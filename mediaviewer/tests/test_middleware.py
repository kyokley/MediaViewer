import pytest
from django.http import HttpResponse

from mediaviewer.middleware import set_secure_headers


@pytest.mark.parametrize("status_code", (200, 502))
def test_secure_headers_preserve_explicit_sensitive_headers(status_code):
    response = HttpResponse(status=status_code)
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    middleware = set_secure_headers(lambda request: response)

    result = middleware(None)

    assert result["Cache-Control"] == "private, no-store"
    assert result["Referrer-Policy"] == "no-referrer"


def test_secure_headers_add_defaults_when_sensitive_headers_are_absent():
    middleware = set_secure_headers(lambda request: HttpResponse())

    response = middleware(None)

    assert response["Cache-Control"] == "no-store"
    assert response["Referrer-Policy"] == "no-referrer, strict-origin-when-cross-origin"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "SAMEORIGIN"


@pytest.mark.parametrize(
    ("preserved_header", "preserved_value", "default_header", "default_value"),
    (
        (
            "Cache-Control",
            "private, no-store",
            "Referrer-Policy",
            "no-referrer, strict-origin-when-cross-origin",
        ),
        ("Referrer-Policy", "no-referrer", "Cache-Control", "no-store"),
    ),
)
def test_secure_headers_preserve_each_header_independently(
    preserved_header, preserved_value, default_header, default_value
):
    response = HttpResponse()
    response[preserved_header] = preserved_value
    middleware = set_secure_headers(lambda request: response)

    result = middleware(None)

    assert result[preserved_header] == preserved_value
    assert result[default_header] == default_value
