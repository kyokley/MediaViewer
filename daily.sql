BEGIN;
    DELETE FROM waiterstatus WHERE datecreated < now() - INTERVAL '14 days';
    DELETE FROM downloadclick WHERE id IN
    (SELECT dc.id FROM downloadclick AS dc
        INNER JOIN downloadtoken AS dt
        ON dt.id = dc.downloadtokenid
        WHERE dt.datecreated < now() - INTERVAL '30 days'
    );
    DELETE FROM downloadtoken WHERE datecreated < now() - INTERVAL '30 days';
COMMIT;

