from mediaviewer.models.downloadclick import DownloadClick
from mediaviewer.models.downloadtoken import DownloadToken
from mediaviewer.models.file import File
from mediaviewer.models.path import Path
from mediaviewer.models.datatransmission import DataTransmission
from mediaviewer.models.error import Error
from mediaviewer.models.filenamescrapeformat import FilenameScrapeFormat
from mediaviewer.models.message import Message

from rest_framework import serializers

class DownloadTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadToken
        fields = ('guid',
                  'userid',
                  'path',
                  'filename',
                  'ismovie',
                  'datecreated',
                  'tokenid',
                  'isvalid',
                  'waitertheme',
                  'displayname',
                  )
    guid = serializers.CharField(required=True,
                                 max_length=32)
    userid = serializers.IntegerField(required=True, source='user.id')
    path = serializers.CharField(required=True)
    filename = serializers.CharField(required=True)
    ismovie = serializers.BooleanField(required=True)
    datecreated = serializers.DateTimeField(required=True)
    tokenid = serializers.IntegerField(required=True, source='id')
    isvalid = serializers.BooleanField(required=True)
    waitertheme = serializers.CharField(required=True)
    displayname = serializers.CharField(required=True)

class DownloadClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadClick
        fields = ('pk',
                  'userid',
                  'filename',
                  'downloadtoken',
                  'datecreated',
                  'size',
                  )

    pk = serializers.ReadOnlyField()
    downloadtoken = serializers.IntegerField(required=True, source='downloadtoken.id')
    userid = serializers.IntegerField(required=True, source='user.id')
    filename = serializers.CharField(required=True)
    datecreated = serializers.DateTimeField(required=True)
    size = serializers.IntegerField(required=True)

class PathSerializer(serializers.ModelSerializer):
    class Meta:
        model = Path
        fields = ('pk',
                  'localpath',
                  'remotepath',
                  'server',
                  'skip',
                  )
    pk = serializers.ReadOnlyField()
    localpath = serializers.CharField(required=True, source='localpathstr')
    remotepath = serializers.CharField(required=True, source='remotepathstr')
    server = serializers.CharField(required=True)
    skip = serializers.IntegerField(required=True)

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('pk',
                  'pathid',
                  'localpath',
                  'filename',
                  'skip',
                  'finished',
                  'size',
                  'streamable',
                  'ismovie',
                  )
    pk = serializers.ReadOnlyField()
    pathid = serializers.IntegerField(required=False, source='path.id')
    localpath = serializers.CharField(required=False, source='path.localpathstr')
    filename = serializers.CharField(required=False)
    skip = serializers.BooleanField(required=False)
    finished = serializers.BooleanField(required=False)
    size = serializers.IntegerField(required=False)
    streamable = serializers.BooleanField(required=False)
    ismovie = serializers.BooleanField(required=False)

class MovieFileSerializer(FileSerializer):
    class Meta:
        model = File
        fields = ('pk',
                  'pathid',
                  'filename',
                  'skip',
                  'finished',
                  'size',
                  )

class DataTransmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataTransmission
        fields = ('pk',
                  'date',
                  'downloaded',
                  )
    pk = serializers.ReadOnlyField()
    downloaded = serializers.DecimalField(max_digits=12, decimal_places=0, required=True)
    date = serializers.DateTimeField(required=True)

class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = ('pk',
                  'date',
                  'error',
                  'ignore',
                  'file',
                  'path',
                  'datatransmission',
                  )
    pk = serializers.ReadOnlyField()
    downloaded = serializers.DecimalField(max_digits=12, decimal_places=0, required=True)
    date = serializers.DateTimeField(required=True)
    error = serializers.CharField(required=True, source='errorstr')
    ignore = serializers.BooleanField(required=True)
    file = serializers.CharField(required=True)
    path = serializers.CharField(required=True)
    datatransmission = serializers.IntegerField(required=True)

class FilenameScrapeFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilenameScrapeFormat
        fields = ('pk',
                  'nameRegex',
                  'seasonRegex',
                  'episodeRegex',
                  'subPeriods',
                  'useSearchTerm',
                  )
    pk = serializers.ReadOnlyField()
    nameRegex = serializers.CharField(required=True)
    episodeRegex = serializers.CharField(required=True)
    seasonRegex = serializers.CharField(required=True)
    subPeriods = serializers.BooleanField(required=True)
    useSearchTerm = serializers.BooleanField(required=True)

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('pk',
                  'touserid',
                  'body',
                  'sent',
                  'level',
                  'datecreated',
                  )
    pk = serializers.ReadOnlyField()
    touserid = serializers.IntegerField(required=True, source='touser.id')
    body = serializers.CharField(required=True)
    sent = serializers.BooleanField(required=True)
    level = serializers.IntegerField(required=True)
    datecreated = serializers.DateTimeField(required=True)
