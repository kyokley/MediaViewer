"""Filename parsing and bounded TheTVDB v4 series lookup."""

import re
from pathlib import PurePath, PureWindowsPath

import requests
from django.conf import settings


_EPISODE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])S[ ._-]*(\d{1,2})[ ._-]*E[ ._-]*(\d{1,2})(?!\d)",
    re.IGNORECASE,
)
_SEPARATORS = re.compile(r"[\s._-]+")
_BASE_URL = "https://api4.thetvdb.com/v4"


def _basename(filename):
    if "\\" in filename:
        return PureWindowsPath(filename).name
    return PurePath(filename).name


def _normalize(value):
    return _SEPARATORS.sub(" ", value).strip().casefold()


def parse_tv_filename(filename):
    """Return (title, season, episode), or None when no valid S/E token exists."""
    if not isinstance(filename, str) or not filename.strip():
        return None

    basename = _basename(filename.strip())
    match = _EPISODE_PATTERN.search(basename)
    if match is None:
        return None

    title = _SEPARATORS.sub(" ", basename[: match.start()]).strip()
    season, episode = (int(value) for value in match.groups())
    if not title or episode == 0:
        return None

    return title, season, episode


def _request_timeout():
    timeout = getattr(settings, "REQUEST_TIMEOUT", None)
    return timeout if isinstance(timeout, (int, float)) and timeout > 0 else 20


def _response_json(response):
    response.raise_for_status()
    return response.json()


def resolve_series_name(title):
    """Return the uniquely matching canonical TheTVDB series name, or None."""
    if not isinstance(title, str) or not title.strip():
        return None

    api_key = getattr(settings, "THETVDB_API_KEY", "")
    if not isinstance(api_key, str) or not api_key.strip():
        return None
    pin = getattr(settings, "THETVDB_PIN", "")
    if not isinstance(pin, str):
        pin = ""

    login_payload = {"apikey": api_key}
    if pin:
        login_payload["pin"] = pin

    timeout = _request_timeout()
    try:
        login_response = requests.post(
            f"{_BASE_URL}/login", json=login_payload, timeout=timeout
        )
        login_data = _response_json(login_response)
        token = login_data.get("data", {}).get("token")
        if not isinstance(token, str) or not token:
            return None

        search_response = requests.get(
            f"{_BASE_URL}/search",
            params={"query": title, "type": "series"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        search_data = _response_json(search_response)
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return None

    results = search_data.get("data") if isinstance(search_data, dict) else None
    if not isinstance(results, list):
        return None

    normalized_title = _normalize(title)
    if not normalized_title:
        return None
    matches = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        result_id = result.get("id")
        name = result.get("name")
        aliases = result.get("aliases", [])
        result_type = result.get("type")
        if (
            not isinstance(result_id, str)
            or not result_id
            or not isinstance(name, str)
            or not name.strip()
            or (aliases is not None and not isinstance(aliases, list))
            or any(not isinstance(alias, str) for alias in (aliases or []))
            or ("type" in result and result_type != "series")
        ):
            continue

        candidate_names = [name, *(aliases or [])]
        if any(_normalize(candidate) == normalized_title for candidate in candidate_names):
            matches.setdefault(result_id, set()).add(name.strip())

    if len(matches) != 1 or len(next(iter(matches.values()))) != 1:
        return None
    return next(iter(next(iter(matches.values()))))
