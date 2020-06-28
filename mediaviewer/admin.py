from django.contrib import admin
from mediaviewer.models.path import Path
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.actor import Actor
from mediaviewer.models.writer import Writer
from mediaviewer.models.director import Director
from mediaviewer.models.genre import Genre
from mediaviewer.models.request import Request
from mediaviewer.models.request import RequestVote
from mediaviewer.models.downloadtoken import DownloadToken


class PathAdmin(admin.ModelAdmin):
    fields = ('remotepathstr',
              'localpathstr',
              'finished',
              'defaultsearchstr',
              'override_display_name',
              'imdb_id',
              )
    list_filter = ('finished',)
    search_fields = ('localpathstr',
                     'remotepathstr',
                     'override_display_name',
                     )
    list_display = ('id',
                    'remotepathstr',
                    'finished',
                    )


@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'displayname',
                    'ismovie',
                    'datecreated',
                    )


admin.site.register(File)
admin.site.register(Path, PathAdmin)
admin.site.register(FilenameScrapeFormat)
admin.site.register(UserSettings)
admin.site.register(PosterFile)
admin.site.register(Actor)
admin.site.register(Writer)
admin.site.register(Director)
admin.site.register(Genre)
admin.site.register(Request)
admin.site.register(RequestVote)
