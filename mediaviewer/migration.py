from django.db import connections
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import ConnectionDoesNotExist
from mediaviewer import models

def setup_cursors():
    try:
        autodlCursor = connections['autodl'].cursor()
    except ConnectionDoesNotExist:
        print("autodl database is not configured")
        raise

    try:
        defaultCursor = connections['default'].cursor()
    except ConnectionDoesNotExist:
        print("default database is not configured")
        raise

    return autodlCursor, defaultCursor

def import_paths():
    autodlCursor, defaultCursor = setup_cursors()
    if autodlCursor is None or defaultCursor is None:
        return

    sql = """SELECT MAX(id) FROM mediaviewer_path"""
    defaultCursor.execute(sql)
    maxID = defaultCursor.fetchone()[0]

    sql = """SELECT id, localpathstr, remotepathstr FROM path """
    if maxID:
        sql += """ WHERE id > %s""" % (maxID)

    autodlCursor.execute(sql)
    rows = autodlCursor.fetchall()
    for idx, row in enumerate(rows):
        print("importing path %s of %s" % (idx + 1, len(rows)))
        path = models.Path(id=row[0], localPath=row[1], remotePath=row[2])
        path.save()

def import_files():
    autodlCursor, defaultCursor = setup_cursors()
    if autodlCursor is None or defaultCursor is None:
        return

    sql = """SELECT MAX(id) FROM mediaviewer_file"""
    defaultCursor.execute(sql)
    maxID = defaultCursor.fetchone()[0]

    sql = """SELECT id,
                    pathid,
                    filename,
                    skip,
                    finished,
                    size,
                    viewed,
                    comment,
                    error FROM file"""
    if maxID:
        sql += """ WHERE id > %s""" % (maxID)

    autodlCursor.execute(sql)
    rows = autodlCursor.fetchall()
    for idx, row in enumerate(rows):
        print("importing file %s of %s" % (idx + 1, len(rows)))
        try:
            path = models.Path.objects.get(id=row[1])
        except ObjectDoesNotExist:
            print("Path not found with id %s" % row[1])
            continue
        else:
            file = models.File(id=row[0],
                               path=path,
                               fileName=row[2],
                               skip=row[3],
                               finished=row[4],
                               size=row[5],
                               viewed=row[6],
                               comment=row[7] or '',
                               error=row[8])
            file.save()

def import_datatransmission():
    autodlCursor, defaultCursor = setup_cursors()
    if autodlCursor is None or defaultCursor is None:
        return

    sql = """SELECT MAX(id) FROM mediaviewer_datatransmission"""
    defaultCursor.execute(sql)
    maxID = defaultCursor.fetchone()[0]

    sql = """SELECT id, date, downloaded FROM datatransmission"""
    if maxID:
        sql += """ WHERE id > %s""" % (maxID)

    autodlCursor.execute(sql)
    rows = autodlCursor.fetchall()
    for idx, row in enumerate(rows):
        print("importing datatransmission %s of %s" % (idx + 1, len(rows)))
        dt = models.DataTransmission(id=row[0],
                                     date=row[1],
                                     transferred=row[2])
        dt.save()

def import_errors():
    autodlCursor, defaultCursor = setup_cursors()
    if autodlCursor is None or defaultCursor is None:
        return

    sql = """SELECT MAX(id) FROM mediaviewer_error"""
    defaultCursor.execute(sql)
    maxID = defaultCursor.fetchone()[0]

    sql = """SELECT id, date, errorstr FROM error"""
    if maxID:
        sql += """ WHERE id > %s""" % (maxID)

    autodlCursor.execute(sql)
    rows = autodlCursor.fetchall()
    for idx, row in enumerate(rows):
        print("importing error %s of %s" % (idx + 1, len(rows)))
        error = models.Error(id=row[0],
                             date=row[1],
                             errorStr=row[2])
        error.save()

def import_all():
    print("import paths")
    import_paths()
    print("import files")
    import_files()
    print("import data transmission")
    import_datatransmission()
    print("import errors")
    import_errors()
    print("done")
