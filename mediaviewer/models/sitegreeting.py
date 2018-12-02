from django.db import models


class SiteGreeting(models.Model):
    greeting = models.TextField(blank=True, null=False, db_column='greeting')
    user = models.ForeignKey('auth.User',
                             null=False,
                             blank=False,
                             db_column='userid')
    datecreated = models.DateTimeField(db_column='datecreated', blank=True)

    class Meta:
        app_label = 'mediaviewer'
        db_table = 'sitegreeting'

    def __unicode__(self):
        return 'id: %s g: %s\nu: %s\nd: %s' % (self.id,
                                               self.greeting,
                                               self.user.id,
                                               self.datecreated)

    @classmethod
    def latestSiteGreeting(cls):
        greetings = cls.objects.order_by('-id')
        return greetings and greetings[0] or None
