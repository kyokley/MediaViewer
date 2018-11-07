from django.db import models
from mediaviewer.models.message import Message


class VideoProgress(models.Model):
    user = models.ForeignKey(
            'auth.User',
            null=False,
            blank=False,
            db_column='userid')
    filename = models.TextField(db_column='filename', null=True)
    hashed_filename = models.TextField(db_column='hashedfilename')
    offset = models.DecimalField(max_digits=9, decimal_places=3)
    date_edited = models.DateTimeField(auto_now=True)
    file = models.ForeignKey('mediaviewer.File', null=True, blank=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'videoprogress'

    def _unicode__(self):
        return 'id: %s f: %s o: %s' % (self.id,
                                       self.filename,
                                       self.offset,
                                       )

    @classmethod
    def new(cls,
            user,
            filename,
            hashed_filename,
            offset,
            file,
            ):
        vp = cls()
        vp.user = user
        vp.filename = filename
        vp.hashed_filename = hashed_filename
        vp.offset = offset
        vp.file = file
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
                       offset,
                       file,
                       ):
        record = (cls.objects.filter(user=user)
                             .filter(hashed_filename=hashed_filename)
                             .first())
        if record:
            record.offset = offset
            record.file = file
            record.save()
        else:
            record = cls.new(user,
                             filename,
                             hashed_filename,
                             offset,
                             file
                             )

        return record

    @classmethod
    def destroy(cls,
                user,
                hashed_filename):
        vp = (cls.objects.filter(user=user)
                         .filter(hashed_filename=hashed_filename)
                         .first())
        if vp:
            if not vp.file.next():
                Message.clearLastWatchedMessage(user)

            vp.delete()
