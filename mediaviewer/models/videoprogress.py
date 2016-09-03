from django.db import models

class VideoProgress(models.model):
    user = models.ForeignKey('auth.User', null=False, blank=False, db_column='userid')
    filename = models.TextField(db_column='filename')
    offset = models.DecimalField(max_digits=9, decimal_places=3)
    date_edited = models.DateTimeField(auto_now=True)

    @classmethod
    def new(cls,
            user,
            filename,
            offset):
        vp = cls()
        vp.user = user
        vp.filename = filename
        vp.save()
        return vp

    @classmethod
    def createOrUpdate(cls,
                       user,
                       filename,
                       offset):
        record = (cls.objects.filter(user=user)
                             .filter(filename=filename)
                             .first())
        if record:
            record.offset = offset
            record.save()
        else:
            record = cls.new(user,
                             filename,
                             offset)
        return record

    @classmethod
    def delete(cls,
               user,
               filename):
        cls.objects.filter(user=user).filter(filename=filename).delete()
