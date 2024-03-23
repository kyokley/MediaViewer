from django.db import models

from mediaviewer.models.message import Message


class VideoProgressManager(models.Manager):
    def destroy(self, user, hashed_filename):
        vp = self.filter(user=user).filter(hashed_filename=hashed_filename).first()
        if vp:
            if vp.media_file and not vp.media_file.next():
                Message.clearLastWatchedMessage(user)

            vp.delete()


class VideoProgress(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        db_column="userid",
    )
    filename = models.TextField(db_column="filename", null=True)
    hashed_filename = models.TextField(db_column="hashedfilename")
    offset = models.DecimalField(max_digits=9, decimal_places=3)
    date_edited = models.DateTimeField(auto_now=True)
    media_file = models.ForeignKey(
        "mediaviewer.MediaFile", on_delete=models.CASCADE, null=True, blank=True
    )
    movie = models.ForeignKey(
        "mediaviewer.Movie", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = VideoProgressManager()

    class Meta:
        app_label = "mediaviewer"
        db_table = "videoprogress"
        verbose_name_plural = "Video Progress"

    def __str__(self):
        return f"id: {self.id} f: {self.filename} o: {self.offset}"
