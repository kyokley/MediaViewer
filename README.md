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

## B2 object key layout

Under the configured prefix, each B2 key adds exactly three MediaPath ID
directories. The positive MediaPath ID is padded to nine decimal digits and
split into three-digit segments: ID `1` uses
`000/000/001/`, ID `1234567` uses `001/234/567/`, and ID `999999999` uses
`999/999/999/`. IDs outside `1` through `999999999` fail closed. Files for a
MediaPath stay together below that three-directory prefix. Files are not
sharded by UUID, and the number of files within a MediaPath directory is not
capped.

The bulk `upload_to_b2` command stores its logical
`<configured-prefix>/<MediaPath-ID>/<local-directory>/` URI unchanged; the
nested object prefix is derived from that URI when files are uploaded or read.

## B2 deletion

Deleting a B2-backed `MediaFile`, including queryset and cascade deletions,
removes its video and its own `subtitle_files` from B2 after the database
transaction commits. Local files and movie subtitles stored on `MediaPath`
are not removed. Cleanup uses the native B2 API to list and permanently delete
all uploaded versions and hide markers for each exact object key; similarly
prefixed objects are not deleted.

The application key needs `listFiles` and `deleteFiles` capabilities for the
bucket and object names being deleted. Object Lock retention or legal holds can
prevent deletion. Cleanup runs synchronously after commit. Failures are logged
without undoing the database deletion, and there is no automatic retry; failed
objects require manual cleanup using the bucket and key in the log.

## File-by-file migration from MediaWaiter

MediaWaiter's `migrate_to_b2.py` requires the staff-only file-migration API.
Deploy this backend and apply database migrations, including
`0075_mediapath_migration_source`, before running the client. Configure
`B2_BUCKET_NAME` and `B2_NAME_PREFIX` on MediaViewer; clients must use the returned
bucket and upload prefix unchanged.

The file-level actions are under `/mediaviewer/api/migrations/`:

- `GET file-candidates/`: cursor-paginated local TV episode and current movie
  candidates with signed source snapshots. `limit` counts videos; each page
  includes `version`, `candidates`, and `next_cursor` (null on the final page).
- `POST {source_pk}/prepare-file/`: validates the source snapshot and complete
  video/subtitle manifest, reserves a TV destination when needed, and returns a
  signed publication token, destination ID, bucket, and upload prefix.
- `POST {source_pk}/publish-file/`: consumes that token after successful uploads,
  publishes atomically, and accepts an exact replay after a lost response.

Check `python manage.py show_urls` in the deployed runtime for all three actions.
The older whole-path `candidates/` and `publish/` actions remain available but are
not interchangeable with this protocol.

The actions use the existing `run/` ownership lock. Pause ordinary writers
externally; the lock does not stop MediaConverter, scrubbing, or other API writes.
The API trusts the authorized client's upload manifest and does not contact B2
to verify object contents. MediaWaiter verifies uploads before publication and
deletes local sources only after confirmed publication and source checks. It has
no persistent journal or automatic crash recovery; keep ordinary writers paused
while investigating failures and inspect publication and ownership before cleanup.

TV preparation creates an unattached B2 MediaPath reservation. Publication
attaches it to the series and moves only the selected existing MediaFile, keeping
its ID and episode metadata. Unselected siblings remain local; later episodes
reuse the reservation. Movies publish their existing MediaPath in place.
Preparation alone does not change playback. Interrupted preparations can leave
unused reservations; those reservations do not represent published videos.

## Duplicate local episode cleanup

Data migration `0076_remove_duplicate_local_mediafiles` targets the two audited
duplicate groups only. It removes MediaFile `7999`, retaining `8001` under
MediaPath `288` (The Chi S01E05), and removes `9955`, retaining `9956` under
MediaPath `378` (Harley Quinn S02E04). The smaller primary key determines which
duplicate is removed; unrelated duplicate groups are not changed.
Targets are identified by record IDs, without hard-coded local filenames. Each
pair must still have matching filenames.

The migration deletes the removed rows' comments/viewed flags, watch progress,
download tokens, and unreferenced episode posters with their metadata links.
Shared posters, users, MediaPaths, TV series, scraper definitions, and metadata
entities remain. It does not delete local media, poster image files, or B2 objects.

Already-absent pairs are left alone. If both rows exist but no longer match the
expected local duplicate group, the migration aborts instead of deleting them.
This data deletion is irreversible: back up the database and pause ordinary
writers before applying it through `python manage.py migrate`.

## Repair legacy apostrophe filename mismatches

Data migration `0077_repair_local_mediafile_filenames` repairs only the 44 audited
MediaFile IDs under MediaPaths `52`, `55`, `112`, `115`, `116`, and `181`. It
removes ASCII apostrophes from their stored filenames to match the confirmed
existing files. No local filenames are embedded in the migration.

Only `MediaFile.filename` changes. Record IDs, timestamps, posters, comments,
watch progress and its hashes, download tokens, and parent associations remain
unchanged. The migration does not rename, read, upload, or delete media files.

Missing or already-corrected targets are skipped. Targets still needing repair
must remain on their expected local TV paths without B2 UUIDs. Existing filename
collisions and collisions between planned repairs abort the entire operation
before any update. Unrelated records are never normalized automatically.

This is an irreversible metadata repair: removing apostrophes loses their
original positions. Back up the database and pause ordinary writers before
applying it through `python manage.py migrate`. The migration trusts the prior
filesystem audit; it does not inspect the media host during deployment.

## Exclude a duplicate legacy movie source

Data migration `0078_skip_duplicate_movie_source` marks only stale MediaPath
`560` as skipped. Active MediaPath `723`, owned by Movie `328`, already represents
the same film. Movie `165` and its history remain intact; this repair does not
merge or delete either movie or create a second owner for the valid directory.

The migration checks ownership, audited path fingerprints, the enabled current
source, and matching poster film identifiers and release dates. Changed or
unexpectedly associated records abort the operation. Missing, already-skipped,
or already-published stale sources are left alone. No private filenames or paths
are embedded in code.

Only the stale source's `skip` flag changes. All other fields, timestamps, viewing
history, tokens, posters, and media files remain unchanged. The migration has no
automatic reverse operation; back up the database and pause ordinary writers
before applying it. Review any future catalog merge separately.
