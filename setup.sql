--This file applies migrations to an existing mediaviewer db.
-- In other words, make sure to run syncdb before applying this file.
BEGIN;
    ALTER TABLE file ADD COLUMN searchstr TEXT DEFAULT NULL;
COMMIT;

BEGIN;
    ALTER TABLE usersettings ADD COLUMN can_download BOOLEAN DEFAULT FALSE;
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN imdb_id TEXT DEFAULT NULL;
COMMIT;

BEGIN;
    ALTER TABLE posterfile ADD COLUMN plot TEXT DEFAULT NULL;
    ALTER TABLE posterfile ADD COLUMN genre TEXT DEFAULT NULL;
    ALTER TABLE posterfile ADD COLUMN actors TEXT DEFAULT NULL;
    ALTER TABLE posterfile ADD COLUMN writer TEXT DEFAULT NULL;
    ALTER TABLE posterfile ADD COLUMN director TEXT DEFAULT NULL;
COMMIT;

BEGIN;
    ALTER TABLE posterfile ADD COLUMN extendedplot TEXT DEFAULT NULL;
COMMIT;

BEGIN;
    UPDATE path SET localpathstr = 'Movies' WHERE localpathstr = 'movie';
    UPDATE path SET remotepathstr = 'Movies' WHERE remotepathstr = 'movie';
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN hide BOOLEAN DEFAULT FALSE;
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN filenamescrapeformatid INTEGER;
    ALTER TABLE file ADD CONSTRAINT file_filenamescrapeformatfk FOREIGN KEY(filenamescrapeformatid) REFERENCES filenamescrapeformat(id);
    ALTER TABLE path ADD COLUMN defaultscraperid INTEGER;
    ALTER TABLE path ADD CONSTRAINT path_filenamescrapeformatfk FOREIGN KEY(defaultscraperid) REFERENCES filenamescrapeformat(id);
COMMIT;

--BEGIN;
--    --*********** Run this only once!!!! ***********
--    INSERT INTO filenamescrapeformat(nameregex,
--                                     seasonregex,
--                                     episoderegex,
--                                     subperiods)
--                                     VALUES
--                                     ('[a-zA-Z\\.]+(?=\\.[sS])',
--                                      '(?<=[sS])\\d+',
--                                      '(?<=[eE])\\d+',
--                                      TRUE);
--COMMIT;

BEGIN;
    ALTER TABLE filenamescrapeformat ADD COLUMN subperiods BOOLEAN DEFAULT TRUE;
COMMIT;

BEGIN;
    UPDATE file SET hide = 't' WHERE id IN (1173, 1159, 1252);
COMMIT;

BEGIN;
    ALTER TABLE filenamescrapeformat ADD COLUMN usesearchterm BOOLEAN DEFAULT FALSE;
COMMIT;

BEGIN;
    TRUNCATE downloadtoken;
    TRUNCATE downloadclick;
    ALTER TABLE downloadclick DROP COLUMN fileid;
    ALTER TABLE downloadtoken ADD COLUMN userid INTEGER;
    ALTER TABLE downloadclick ADD COLUMN size INTEGER;
    ALTER TABLE downloadclick ADD COLUMN downloadtokenid INTEGER;
    ALTER TABLE downloadclick ADD COLUMN filename TEXT;
    ALTER TABLE downloadclick ADD CONSTRAINT downloadclick_downloadtokenfk FOREIGN KEY(downloadtokenid) REFERENCES downloadtoken(id);
COMMIT;

BEGIN;
    ALTER TABLE usersettings ADD COLUMN site_theme TEXT DEFAULT 'default';
COMMIT;

BEGIN;
    ALTER TABLE waiterstatus ADD COLUMN failurereason TEXT;
COMMIT;

BEGIN;
    DROP TABLE "BruteBuster_failedattempt";
COMMIT;

BEGIN;
    ALTER TABLE path ADD COLUMN tvdb_id TEXT DEFAULT NULL;
    ALTER TABLE posterfile ADD COLUMN pathid INTEGER NULL;
COMMIT;

BEGIN;
    TRUNCATE posterfile;
COMMIT;

BEGIN;
    ALTER TABLE downloadclick ALTER COLUMN size TYPE BIGINT;
COMMIT;

BEGIN;
    ALTER TABLE posterfile ADD COLUMN episodename TEXT DEFAULT NULL;
COMMIT;

BEGIN;
    ALTER TABLE usersettings ADD COLUMN default_sort TEXT default 'filename';
COMMIT;

BEGIN;
    ALTER TABLE downloadtoken ADD COLUMN waiter_theme TEXT DEFAULT 'default';
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN ismovie BOOLEAN;
COMMIT;

BEGIN;
    ALTER TABLE path ADD COLUMN defaultsearchstr TEXT;
COMMIT;

BEGIN;
    ALTER TABLE downloadtoken ADD COLUMN display_name TEXT;
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN streamable BOOLEAN DEFAULT false;
COMMIT;

BEGIN;
    ALTER TABLE downloadtoken ADD COLUMN fileid INTEGER;
    ALTER TABLE downloadtoken ADD CONSTRAINT downloadtoken_filefk FOREIGN KEY(fileid) REFERENCES file(id);
COMMIT;

BEGIN;
    ALTER TABLE path ADD COLUMN imdb_id TEXT;
COMMIT;

BEGIN;
    ALTER TABLE file ADD COLUMN override_filename TEXT;
    ALTER TABLE file ADD COLUMN override_season TEXT;
    ALTER TABLE file ADD COLUMN override_episode TEXT;
COMMIT;

BEGIN;
    UPDATE file SET override_filename = '' WHERE override_filename IS NULL;
    UPDATE file SET override_season = '' WHERE override_season IS NULL;
    UPDATE file SET override_episode = '' WHERE override_episode IS NULL;
    ALTER TABLE file ALTER COLUMN override_filename SET DEFAULT '';
    ALTER TABLE file ALTER COLUMN override_season SET DEFAULT '';
    ALTER TABLE file ALTER COLUMN override_episode SET DEFAULT '';
COMMIT;

BEGIN;
    ALTER TABLE posterfile ADD COLUMN rating TEXT;
    ALTER TABLE posterfile ADD COLUMN rated TEXT;
COMMIT;

BEGIN;
ALTER TABLE file ALTER COLUMN datecreated TYPE timestamptz
USING to_timestamp(datecreated, 'YYYY-MM-DD HH24:MI:SS');

ALTER TABLE file ALTER COLUMN dateedited TYPE timestamptz
USING to_timestamp(dateedited, 'YYYY-MM-DD HH24:MI:SS');

ALTER TABLE file ALTER COLUMN finished DROP DEFAULT;
ALTER TABLE file ALTER COLUMN finished TYPE bool USING CASE WHEN finished = 0 THEN FALSE ELSE TRUE END;
ALTER TABLE file ALTER COLUMN finished SET DEFAULT FALSE;

ALTER TABLE file ALTER COLUMN skip DROP DEFAULT;
ALTER TABLE file ALTER COLUMN skip TYPE bool USING CASE WHEN skip = 0 THEN FALSE ELSE TRUE END;
ALTER TABLE file ALTER COLUMN skip SET DEFAULT FALSE;

ALTER TABLE file DROP COLUMN viewed;
ALTER TABLE file DROP COLUMN errorid;

UPDATE file SET datecreated = '2013-09-19 06:43:17' WHERE datecreated IS NULL OR datecreated < '2013-09-19 06:43:17';
UPDATE file SET dateedited = '2013-09-19 06:43:17' WHERE dateedited IS NULL OR dateedited < '2013-09-19 06:43:17';

ALTER TABLE file ALTER COLUMN datecreated SET DEFAULT now();
ALTER TABLE file ALTER COLUMN datecreated SET NOT NULL;
ALTER TABLE file ALTER COLUMN dateedited SET DEFAULT now();
ALTER TABLE file ALTER COLUMN dateedited SET NOT NULL;

ALTER TABLE path ALTER COLUMN skip DROP DEFAULT;
ALTER TABLE path ALTER COLUMN skip TYPE bool USING CASE WHEN skip = 0 THEN FALSE ELSE TRUE END;
ALTER TABLE path ALTER COLUMN skip SET DEFAULT FALSE;
ALTER TABLE path ADD COLUMN lastcreatedfiledate timestamptz;
UPDATE path SET lastcreatedfiledate = (SELECT max(datecreated) FROM file WHERE file.pathid = path.id);
COMMIT;

BEGIN;
    ALTER TABLE path ADD COLUMN ismovie BOOLEAN NOT NULL DEFAULT FALSE;
    UPDATE path SET ismovie = TRUE WHERE localpathstr = 'Movies' AND remotepathstr = 'Movies';
COMMIT;

BEGIN;
    ALTER TABLE file DROP COLUMN ismovie;
COMMIT;

BEGIN;
    ALTER TABLE usersettings ADD COLUMN auto_download BOOLEAN NOT NULL DEFAULT FALSE;
COMMIT;

BEGIN;
    ALTER TABLE path ADD COLUMN display_name TEXT;
COMMIT;

BEGIN;
    ALTER TABLE usersettings ADD COLUMN force_password_change BOOLEAN NOT NULL DEFAULT FALSE;
COMMIT;

BEGIN;
    CREATE UNIQUE INDEX email_unique_idx ON auth_user(LOWER(email)) WHERE email != '';
COMMIT;
