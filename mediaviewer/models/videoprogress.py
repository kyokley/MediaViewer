from django.db import models

class VideoProgress(models.Model):
    user = models.ForeignKey('auth.User', null=False, blank=False, db_column='userid')
    filename = models.TextField(db_column='filename', null=True)
    hashed_filename = models.TextField(db_column='hashedfilename')
    offset = models.DecimalField(max_digits=9, decimal_places=3)
    date_edited = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'videoprogress'

    @classmethod
    def new(cls,
            user,
            filename,
            hashed_filename,
            offset):
        vp = cls()
        vp.user = user
        vp.filename = filename
        vp.hashed_filename = hashed_filename
        vp.offset = offset
        vp.save()
        return vp

    @classmethod
    def get(cls, user, hashed_filename):
        vp = (cls.objects.filter(user=user)
                         .filter(hashed_filename=hashed_filename)
                         .first())
        return vp

    @classmethod
    def createOrUpdate(cls,
                       user,
                       filename,
                       hashed_filename,
                       offset):
        record = (cls.objects.filter(user=user)
                             .filter(hashed_filename=hashed_filename)
                             .first())
        if record:
            record.offset = offset
            record.save()
        else:
            record = cls.new(user,
                             filename,
                             hashed_filename,
                             offset)
        return record

    @classmethod
    def delete(cls,
               user,
               hashed_filename):
        cls.objects.filter(user=user).filter(hashed_filename=hashed_filename).delete()
