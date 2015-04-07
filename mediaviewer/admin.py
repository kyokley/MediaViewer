from django.contrib import admin
#from mediaviewer.models import File, Path, FilenameScrapeFormat, UserSettings
from mediaviewer.models.path import Path
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.usersettings import UserSettings
from mediaviewer.models.file import File

admin.site.register(File)
admin.site.register(Path)
admin.site.register(FilenameScrapeFormat)
admin.site.register(UserSettings)
