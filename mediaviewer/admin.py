from django.contrib import admin
#from mediaviewer.models import File, Path, FilenameScrapeFormat, UserSettings
from mediaviewer.models.path import Path
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.file import File
from mediaviewer.models.posterfile import PosterFile
from mediaviewer.models.actor import Actor
from mediaviewer.models.writer import Writer
from mediaviewer.models.director import Director
from mediaviewer.models.genre import Genre

admin.site.register(File)
admin.site.register(Path)
admin.site.register(FilenameScrapeFormat)
admin.site.register(UserSettings)
admin.site.register(PosterFile)
admin.site.register(Actor)
admin.site.register(Writer)
admin.site.register(Director)
admin.site.register(Genre)
