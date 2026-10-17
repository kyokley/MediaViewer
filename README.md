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

## B2 TV episode metadata

New UUID TV uploads infer season and episode locally from the logical filename,
not the UUID object key. Recognized episodes receive a linked poster, followed
by best-effort episode metadata enrichment after the upload transaction commits.
Enrichment runs synchronously in the request's commit path and can increase
upload response latency. Metadata request failures do not undo the committed
upload.

Normal successful uploads do not require a `generateposters` run. That command
remains available to retry missing metadata. The repository does not configure a
schedule for this command; deployments must invoke it manually or supply their
own scheduler. The command can process unrelated incomplete posters and makes
external requests.

Existing uploads are not repaired by replaying the upload request. Any backfill
for affected UUID TV records remains a separate, explicit operation and has not
been performed here. Local episode inference preserves existing coordinates and
poster contents; unrecognized filenames still need manual correction. Avoid
`infer_scraper()` for this repair because it deletes the existing poster before
inference.
