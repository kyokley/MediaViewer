from django.contrib import admin
from mediaviewer.models import Genre
from mediaviewer.models import Path
from mediaviewer.models import FilenameScrapeFormat
from mediaviewer.models import UserSettings
from mediaviewer.models import File
from mediaviewer.models import PosterFile
from mediaviewer.models import Request
from mediaviewer.models import DownloadToken
from mediaviewer.models import DonationSite
from mediaviewer.models import VideoProgress
from mediaviewer.models import SiteGreeting
from mediaviewer.models import TV, Movie, MediaFile, MediaPath


@admin.register(Path)
class PathAdmin(admin.ModelAdmin):
    fields = (
        "remotepathstr",
        "localpathstr",
        "finished",
        "defaultsearchstr",
        "override_display_name",
        "imdb_id",
    )
    list_filter = ("finished",)
    search_fields = (
        "localpathstr",
        "remotepathstr",
        "override_display_name",
    )
    list_display = (
        "id",
        "remotepathstr",
        "finished",
    )


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "filename",
        "hide",
        "datecreated",
    )
    search_fields = (
        "id",
        "filename",
    )


@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "displayname",
        "ismovie",
        "datecreated",
    )
    search_fields = (
        "id",
        "displayname",
        "user__username",
    )


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "done",
        "datecreated",
    )
    ordering = ("-datecreated",)


@admin.register(FilenameScrapeFormat)
class FilenameScrapeFormatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nameRegex",
        "seasonRegex",
        "episodeRegex",
        "subPeriods",
        "useSearchTerm",
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "last_watched",
    )
    search_fields = ("user__username",)
    ordering = ("user__username",)


@admin.register(PosterFile)
class PosterFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "filename",
        "pathname",
        "poster_url",
    )


@admin.register(DonationSite)
class DonationSiteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "site_name",
        "url",
    )


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "file_filename",
        "offset",
    )

    def file_filename(self, obj):
        return f"{obj.file.filename}"

    file_filename.short_description = "File"


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "genre",
    )
    search_fields = (
        "id",
        "genre",
    )


@admin.register(SiteGreeting)
class SiteGreetingAdmin(admin.ModelAdmin):
    ordering = ("-id",)


class MediaPathInline(admin.TabularInline):
    model = MediaPath
    readonly_fields = ['tv', 'movie']
    show_change_link = True


@admin.register(TV)
class TVAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'finished',
        'imdb',
        'tvdb',
    )
    search_fields = (
        "name",
    )
    list_filter = ("finished",)
    inlines = [MediaPathInline]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'finished',
        'imdb',
    )
    search_fields = (
        "name",
    )
    list_filter = ("finished",)
    inlines = [MediaPathInline]


class MediaFileInline(admin.StackedInline):
    model = MediaFile
    show_change_link = True
    ordering = ('override_season', 'override_episode')


@admin.register(MediaPath)
class MediaPathAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'path',
        'tv',
        'movie',
        'skip',
    )
    search_fields = (
        '_path',
    )
    list_filter = ("skip",)
    inlines = [MediaFileInline]


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'filename',
        'override_display_name',
        'media_path',
        'hide',
    )
    search_fields = (
        "filename",
    )
    list_filter = ("hide",)


admin.site.site_url = "/mediaviewer"
