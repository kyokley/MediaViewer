from django.db import models


class SiteGreeting(models.Model):
    greeting = models.TextField(blank=True, null=False, db_column="greeting")
    datecreated = models.DateTimeField(
        db_column="datecreated", blank=True, auto_now_add=True
    )

    class Meta:
        app_label = "mediaviewer"
        db_table = "sitegreeting"

    def __str__(self):
        return f"id: {self.id} g: {self.greeting}\nd: {self.datecreated}"

    @classmethod
    def latestSiteGreeting(cls):
        greetings = cls.objects.order_by("-id")
        return greetings and greetings[0] or None

    @classmethod
    def new(cls, greeting):
        new_obj = cls()
        new_obj.greeting = greeting
        new_obj.save()
        return new_obj
