import random
from django.db import models

sys_random = random.SystemRandom()


class DonationSiteManager(models.Manager):
    def random(self):
        count = self.count()
        if count:
            rand_idx = sys_random.randint(0, count - 1)
            return self.all()[rand_idx]
        return None


class DonationSite(models.Model):
    objects = DonationSiteManager()

    site_name = models.TextField(blank=False)
    url = models.URLField(blank=False)

    class Meta:
        app_label = 'mediaviewer'
