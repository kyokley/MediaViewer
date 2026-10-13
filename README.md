# MediaViewer [![Docker Image CI](https://github.com/kyokley/MediaViewer/actions/workflows/publish.yml/badge.svg)](https://github.com/kyokley/MediaViewer/actions/workflows/publish.yml)
Website to track tv shows and movies

## TheTVDB filename inference

TV filename inference parses the title and `SxxEyy` episode marker locally, then
uses TheTVDB v4 to resolve the canonical series name. Configure
`THETVDB_API_KEY` with a TheTVDB API key to enable lookup. `THETVDB_PIN` is
optional and is sent only when configured. Missing credentials, network/API
errors, malformed results, or ambiguous matches leave inference unresolved.

These settings are separate from `TVDB_API_KEY` and the existing `API_KEY`,
which remain in use by the existing TMDb-backed metadata helpers. When
inference creates a B2 media path, it preserves any existing local path and
uses `B2_BUCKET_NAME` and `B2_NAME_PREFIX` for the B2 location. The infer API
response shape remains unchanged.
