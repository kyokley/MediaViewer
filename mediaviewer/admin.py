from django.contrib import admin
from mediaviewer.models.path import Path
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.request import Request
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.donation_site import DonationSite


@admin.register(Path)
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


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'filename',
                    'displayName',
                    'hide',
                    'datecreated',
                    )


@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'displayname',
                    'ismovie',
                    'datecreated',
                    )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'name',
                    'done',
                    'datecreated',
                    )
    ordering = ('-datecreated',)


@admin.register(FilenameScrapeFormat)
class FilenameScrapeFormatAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'nameRegex',
                    'seasonRegex',
                    'episodeRegex',
                    'subPeriods',
                    'useSearchTerm',
                    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'user',
                    'last_watched',
                    )


@admin.register(PosterFile)
class PosterFileAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'filename',
                    'pathname',
                    'poster_url',
                    )


@admin.register(DonationSite)
class DonationSiteAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'site_name',
                    'url',
                    )
