import pytest
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django_htmx.http import HttpResponseClientRedirect

from mediaviewer.middleware import AutoLogout, app_html_responses, set_secure_headers


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


@pytest.mark.parametrize(
    ("path", "content_type", "expected_vary"),
    (
        ("/mediaviewer/movies/", "text/html; charset=utf-8", True),
        ("/mediaviewer/b2player/abc123/", "text/html; charset=utf-8", True),
        ("/mediaviewer/b2player/abc123/media/", "application/json", False),
        ("/mediaviewer/b2player/abc123/captions/", "application/json", False),
        ("/mediaviewer/api/movies/", "application/json", False),
        ("/mediaviewer/ajax/movies/", "application/json", False),
        ("/static/app.js", "text/html", False),
    ),
)
def test_app_html_responses_vary_on_htmx_representation_headers(
    path, content_type, expected_vary
):
    request = HttpRequest()
    request.path = path
    response = HttpResponse(content_type=content_type)

    result = app_html_responses(lambda request: response)(request)

    assert ("HX-Request" in result.get("Vary", "")) is expected_vary
    assert ("HX-History-Restore-Request" in result.get("Vary", "")) is expected_vary


def test_app_html_responses_convert_internal_htmx_redirect_and_preserve_cookies():
    request = HttpRequest()
    request.path = "/mediaviewer/settings/"
    request.headers = {"HX-Request": "true"}
    response = HttpResponseRedirect("/mediaviewer/login/?next=/mediaviewer/settings/")
    response["Cache-Control"] = "private, no-store"
    response.set_cookie("sessionid", "session-value", httponly=True)

    result = app_html_responses(lambda request: response)(request)

    assert isinstance(result, HttpResponseClientRedirect)
    assert result["HX-Redirect"] == "/mediaviewer/login/?next=/mediaviewer/settings/"
    assert result["Cache-Control"] == "private, no-store"
    assert result.cookies["sessionid"].value == "session-value"


def test_app_html_responses_do_not_convert_native_boundary_redirects():
    request = HttpRequest()
    request.path = "/mediaviewer/download/"
    request.headers = {"HX-Request": "true"}
    response = HttpResponseRedirect("https://downloads.example.test/file")

    result = app_html_responses(lambda request: response)(request)

    assert result.status_code == 302


def test_app_html_responses_leave_player_redirect_native():
    request = HttpRequest()
    request.path = "/mediaviewer/moviedetail/42/"
    request.headers = {"HX-Request": "true"}
    response = HttpResponseRedirect("/mediaviewer/b2player/abc123/")

    result = app_html_responses(lambda request: response)(request)

    assert result.status_code == 302


def test_app_html_responses_do_not_convert_regular_internal_redirects():
    request = HttpRequest()
    request.path = "/mediaviewer/tvshows/"
    request.headers = {"HX-Request": "true"}
    response = HttpResponseRedirect("/mediaviewer/tvshows/summary/")

    result = app_html_responses(lambda request: response)(request)

    assert result.status_code == 302


def test_auto_logout_returns_home_redirect_after_expiring_session(mocker):
    request = HttpRequest()
    request.user = mocker.Mock(is_authenticated=True)
    request.session = {"last_touch": "2000-01-01T00:00:00"}
    mocker.patch(
        "mediaviewer.middleware.auth.logout",
        side_effect=lambda request: request.session.clear(),
    )

    response = AutoLogout(lambda request: pytest.fail("expired request continued"))(
        request
    )

    assert response.status_code == 302
    assert response["Location"] == "/mediaviewer/"
    assert "last_touch" not in request.session


def test_auto_logout_htmx_response_becomes_client_redirect(mocker):
    request = HttpRequest()
    request.path = "/mediaviewer/movies/"
    request.headers = {"HX-Request": "true"}
    request.user = mocker.Mock(is_authenticated=True)
    request.session = {"last_touch": "2000-01-01T00:00:00"}
    mocker.patch(
        "mediaviewer.middleware.auth.logout",
        side_effect=lambda request: request.session.clear(),
    )

    response = app_html_responses(
        AutoLogout(lambda request: pytest.fail("expired request continued"))
    )(request)

    assert isinstance(response, HttpResponseClientRedirect)
    assert response["HX-Redirect"] == "/mediaviewer/"
