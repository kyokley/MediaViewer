begin;
ALTER TABLE file ALTER COLUMN datecreated type timestamp
using to_timestamp(datecreated, 'YYYY-MM-DD HH24:MI:SS');

ALTER TABLE file ALTER COLUMN dateedited type timestamp
using to_timestamp(dateedited, 'YYYY-MM-DD HH24:MI:SS');

alter table file alter column finished drop default;
ALTER TABLE file ALTER column finished TYPE bool USING CASE WHEN finished = 0 THEN FALSE ELSE TRUE END;
alter table file alter column finished set default false;

alter table file alter column skip drop default;
ALTER TABLE file ALTER column skip TYPE bool USING CASE WHEN skip = 0 THEN FALSE ELSE TRUE END;
alter table file alter column skip set default false;

alter table file drop column viewed;
alter table file drop column errorid;

update file set datecreated = '2013-09-19 06:43:17' where datecreated is null or datecreated < '2013-09-19 06:43:17';
update file set dateedited = '2013-09-19 06:43:17' where dateedited is null or dateedited < '2013-09-19 06:43:17';
commit;
