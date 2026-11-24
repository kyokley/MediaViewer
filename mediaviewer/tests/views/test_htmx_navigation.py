import re
from html.parser import HTMLParser

import pytest
from django.test import Client
from django.urls import reverse

from mediaviewer.models import DownloadToken
from mediaviewer.models.usersettings import UserSettings


def _body(response):
    return response.content.decode(response.charset or "utf-8")


def _title(content):
    match = re.search(
        r"<title[^>]*>(.*?)</title>", content, flags=re.IGNORECASE | re.DOTALL
    )
    assert match is not None
    return " ".join(match.group(1).split())


def _vary_headers(response):
    return {header.strip().lower() for header in response.get("Vary", "").split(",")}


class _CsrfFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form_attrs = []
        self.csrf_token = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.form_attrs.append(attrs)
        if tag == "input" and attrs.get("name") == "csrfmiddlewaretoken":
            self.csrf_token = attrs.get("value")


@pytest.fixture
def b2_player(create_user, create_tv_media_file):
    user = create_user()
    media_file = create_tv_media_file(filename="episode.mkv")
    media_path = media_file.media_path
    media_path._path = "b2://test-bucket/episodes"
    media_path.save(update_fields=("_path",))
    return user, media_file, DownloadToken.objects.from_media_file(user, media_file)


@pytest.mark.django_db
def test_representative_pages_render_full_documents_and_htmx_fragments(
    client, b2_player, mocker
):
    mocker.patch("mediaviewer.models.media.Media._populate_poster")
    user, _, player_token = b2_player
    client.force_login(user)
    urls = (
        reverse("mediaviewer:home"),
        reverse("mediaviewer:movies"),
        reverse("mediaviewer:tvshowsummary"),
        reverse("mediaviewer:requests"),
        reverse("mediaviewer:settings"),
        reverse("mediaviewer:b2player", args=(player_token.guid,)),
    )

    for url in urls:
        full = client.get(url)
        full_body = _body(full)
        assert full.status_code == 200, url
        assert "<!doctype html>" in full_body.lower(), url
        assert 'id="app-content"' in full_body, url
        expected_referrer = "no-referrer" if "b2player" in url else "same-origin"
        assert f'<meta name="referrer" content="{expected_referrer}">' in full_body
        assert _title(full_body), url
        assert (
            len(re.findall(r'<script[^>]+src="[^"]*assets/mediaviewer\.js"', full_body))
            == 1
        )
        assert {"hx-request", "hx-history-restore-request"} <= _vary_headers(full), url

        fragment = client.get(url, HTTP_HX_REQUEST="true")
        fragment_body = _body(fragment)
        assert fragment.status_code == 200, url
        assert "<!doctype html>" not in fragment_body.lower(), url
        assert 'id="app-content"' in fragment_body, url
        assert _title(fragment_body) == _title(full_body), url
        assert not re.findall(r"<script\b[^>]*\bsrc=", fragment_body), url


@pytest.mark.django_db
def test_history_restore_request_returns_full_document_even_with_hx_request(
    client, create_user
):
    client.force_login(create_user())
    response = client.get(
        reverse("mediaviewer:movies"),
        HTTP_HX_REQUEST="true",
        HTTP_HX_HISTORY_RESTORE_REQUEST="true",
    )
    content = _body(response)

    assert response.status_code == 200
    assert "<!doctype html>" in content.lower()
    assert "<html" in content
    assert 'id="app-content"' in content
    assert _title(content)
    assert (
        len(re.findall(r'<script[^>]+src="[^"]*assets/mediaviewer\.js"', content)) == 1
    )


@pytest.mark.django_db
def test_player_media_captions_and_json_responses_do_not_vary_on_htmx(
    client, b2_player, mocker
):
    user, _, token = b2_player
    client.force_login(user)
    mocker.patch(
        "mediaviewer.models.core.ViewableObjectMixin.downloadLink",
        return_value="https://signed.example.test/media",
    )
    mocker.patch(
        "mediaviewer.api.serializers.DownloadTokenSerializer.get_subtitle_files",
        return_value=[],
    )

    media_response = client.get(
        reverse("mediaviewer:b2playermedia", args=(token.guid,)),
        HTTP_HX_REQUEST="true",
    )
    captions_response = client.post(
        reverse("mediaviewer:b2playercaptions", args=(token.guid,)),
        {"captions_enabled": "true"},
        HTTP_HX_REQUEST="true",
    )
    json_response = client.get(
        reverse(
            "mediaviewer:ajaxvideoprogress",
            kwargs={"guid": token.guid, "hashed_filename": "test-hash"},
        ),
        HTTP_HX_REQUEST="true",
    )

    assert media_response.status_code == 200
    assert captions_response.status_code == 204
    assert json_response.status_code == 200
    for response in (media_response, captions_response, json_response):
        assert "hx-request" not in _vary_headers(response)
        assert "hx-history-restore-request" not in _vary_headers(response)


@pytest.mark.django_db
def test_unauthorized_htmx_navigation_uses_client_redirect(client):
    response = client.get(
        reverse("mediaviewer:settings"),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert response["HX-Redirect"].startswith("/mediaviewer/login/")
    assert "Location" not in response
    assert 'id="app-content"' not in _body(response)


@pytest.mark.django_db
def test_expired_htmx_session_uses_configured_client_redirect(client, create_user):
    client.force_login(create_user())
    session = client.session
    session["last_touch"] = "2000-01-01T00:00:00"
    session.save()

    response = client.get(reverse("mediaviewer:movies"), HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("mediaviewer:home")
    assert "Location" not in response
    assert 'id="app-content"' not in _body(response)


@pytest.mark.django_db
def test_settings_csrf_and_method_safety_for_htmx_form(create_user):
    user = create_user()
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    settings = user.settings()
    settings.refresh_from_db()
    initial_theme = settings.theme

    page = client.get(reverse("mediaviewer:settings"))
    page_body = _body(page)
    parser = _CsrfFormParser()
    parser.feed(page_body)
    assert any(form.get("hx-push-url") == "false" for form in parser.form_attrs)
    assert parser.csrf_token

    get_response = client.get(reverse("mediaviewer:submitsettings"))
    settings.refresh_from_db()
    assert get_response.status_code == 405
    assert settings.theme == initial_theme

    invalid = client.post(
        reverse("mediaviewer:submitsettings"),
        {"theme": UserSettings.LIGHT},
        HTTP_HX_REQUEST="true",
    )
    settings.refresh_from_db()
    assert invalid.status_code == 403
    assert settings.theme == initial_theme

    valid = client.post(
        reverse("mediaviewer:submitsettings"),
        {"theme": UserSettings.LIGHT, "csrfmiddlewaretoken": parser.csrf_token},
        HTTP_HX_REQUEST="true",
    )
    settings.refresh_from_db()
    valid_body = _body(valid)

    assert valid.status_code == 200
    assert 'id="app-content"' in valid_body
    assert "<!doctype html>" not in valid_body.lower()
    assert "Settings Saved!" in valid_body
    assert settings.theme == UserSettings.LIGHT


@pytest.mark.django_db
def test_password_reset_keeps_native_csrf_post_origin(create_user, mailoutbox):
    user = create_user()
    client = Client(enforce_csrf_checks=True)

    page = client.get(reverse("mediaviewer:password_reset"))
    page_body = _body(page)
    parser = _CsrfFormParser()
    parser.feed(page_body)

    assert page.status_code == 200
    assert '<meta name="referrer" content="same-origin">' in page_body
    assert any(
        form.get("method", "").lower() == "post" and form.get("hx-boost") == "false"
        for form in parser.form_attrs
    )
    assert parser.csrf_token

    missing_token = client.post(
        reverse("mediaviewer:password_reset"),
        {"email": user.email},
        HTTP_ORIGIN="http://testserver",
    )
    invalid_token = client.post(
        reverse("mediaviewer:password_reset"),
        {"email": user.email, "csrfmiddlewaretoken": "invalid-token"},
        HTTP_ORIGIN="http://testserver",
    )
    assert missing_token.status_code == 403
    assert invalid_token.status_code == 403

    valid = client.post(
        reverse("mediaviewer:password_reset"),
        {"email": user.email, "csrfmiddlewaretoken": parser.csrf_token},
        HTTP_ORIGIN="http://testserver",
    )
    assert valid.status_code == 302
    assert valid["Location"] == reverse("mediaviewer:password_reset_done")
    assert len(mailoutbox) == 1

    rejected = client.post(
        reverse("mediaviewer:password_reset"),
        {"email": user.email, "csrfmiddlewaretoken": parser.csrf_token},
        HTTP_ORIGIN="null",
    )
    assert rejected.status_code == 403
