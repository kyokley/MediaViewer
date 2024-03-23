from django.contrib import admin
from django.db import transaction

from mediaviewer.models import (TV, DonationSite, DownloadToken,
                                FilenameScrapeFormat, Genre, MediaFile,
                                MediaPath, Movie, Poster, Request,
                                SiteGreeting, UserSettings, VideoProgress)


@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "displayname",
        "ismovie",
        "date_created",
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
        "last_watched_tv",
        "last_watched_movie",
    )
    search_fields = ("user__username",)
    ordering = ("user__username",)


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
    readonly_fields = ["tv", "movie"]
    show_change_link = True
    extra = 0


@admin.register(TV)
class TVAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "finished",
    )
    search_fields = ("name",)
    list_filter = ("finished",)
    inlines = [MediaPathInline]


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "finished",
    )
    search_fields = ("name",)
    list_filter = ("finished",)
    inlines = [MediaPathInline]


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    show_change_link = True
    ordering = ("season", "episode")
    extra = 0
    raw_id_fields = ('scraper',
                     '_poster',
                     )


@admin.register(MediaPath)
class MediaPathAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "path",
        "tv",
        "movie",
        "skip",
    )
    search_fields = ("_path",)
    list_filter = ("skip",)
    inlines = [MediaFileInline]


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "filename",
        "display_name",
        "media_path",
        "hide",
    )
    search_fields = ("filename",)
    list_filter = ("hide",)


@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "season",
        "episode",
        "ref_obj",
        "imdb",
        "tmdb",
        "has_image",
    )
    search_fields = (
        "tv__name",
        "movie__name",
        "media_file__filename",
    )
    ordering = ("-id",)
    actions = ("repopulate_data", "clear_and_populate")

    def _populate(self, queryset):
        for poster in queryset:
            with transaction.atomic():
                poster._populate_data()
                poster.save()

    def repopulate_data(self, request, queryset):
        self._populate(queryset)

    repopulate_data.description = "Re-populate Data"

    def clear_and_populate(self, request, queryset):
        queryset.update(imdb="", tmdb="")
        self._populate(queryset)

    clear_and_populate.description = "Clear and Populate"


admin.site.site_url = "/mediaviewer"
