# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-16 12:52
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import mediaviewer.models.downloadtoken


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataTransmission',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('datestr', models.DateField(blank=True, db_column='date')),
                ('downloaded', models.DecimalField(blank=True, decimal_places=1000, max_digits=1000, null=True)),
            ],
            options={
                'db_table': 'datatransmission',
            },
        ),
        migrations.CreateModel(
            name='DownloadClick',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.TextField(blank=True, db_column='filename')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('size', models.BigIntegerField(db_column='size')),
            ],
            options={
                'db_table': 'downloadclick',
            },
        ),
        migrations.CreateModel(
            name='DownloadToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guid', models.CharField(default=mediaviewer.models.downloadtoken._createId, max_length=32, unique=True)),
                ('path', models.TextField(db_column='path')),
                ('filename', models.TextField(db_column='filename')),
                ('ismovie', models.BooleanField(db_column='ismovie')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('waitertheme', models.TextField(db_column='waiter_theme')),
                ('displayname', models.TextField(db_column='display_name')),
            ],
            options={
                'db_table': 'downloadtoken',
            },
        ),
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('datecreatedstr', models.DateTimeField(blank=True, db_column='datecreated')),
                ('errorstr', models.TextField(blank=True)),
                ('ignore', models.BooleanField(db_column='ignore')),
                ('datatransmission', models.ForeignKey(blank=True, db_column='datatransmissionid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.DataTransmission')),
            ],
            options={
                'db_table': 'error',
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.TextField(blank=True)),
                ('skip', models.BooleanField()),
                ('finished', models.BooleanField()),
                ('size', models.IntegerField(blank=True, null=True)),
                ('datecreated', models.DateTimeField(auto_now_add=True)),
                ('dateedited', models.DateTimeField(auto_now=True)),
                ('_searchString', models.TextField(blank=True, db_column='searchstr', null=True)),
                ('imdb_id', models.TextField(blank=True, db_column='imdb_id', null=True)),
                ('hide', models.BooleanField(db_column='hide', default=False)),
                ('streamable', models.BooleanField(db_column='streamable', default=True)),
                ('override_filename', models.TextField(blank=True)),
                ('override_season', models.TextField(blank=True)),
                ('override_episode', models.TextField(blank=True)),
                ('datatransmission', models.ForeignKey(blank=True, db_column='datatransmissionid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.DataTransmission')),
            ],
            options={
                'db_table': 'file',
            },
        ),
        migrations.CreateModel(
            name='FilenameScrapeFormat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nameRegex', models.TextField(blank=True, db_column='nameregex', null=True)),
                ('seasonRegex', models.TextField(blank=True, db_column='seasonregex', null=True)),
                ('episodeRegex', models.TextField(blank=True, db_column='episoderegex', null=True)),
                ('subPeriods', models.BooleanField(db_column='subperiods')),
                ('useSearchTerm', models.BooleanField(db_column='usesearchterm')),
            ],
            options={
                'db_table': 'filenamescrapeformat',
            },
        ),
        migrations.CreateModel(
            name='LoginEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(db_column='datecreated')),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'loginevent',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(blank=True, db_column='body')),
                ('sent', models.BooleanField(db_column='sent')),
                ('level', models.IntegerField(db_column='level')),
                ('datecreated', models.DateTimeField(db_column='datecreated')),
                ('touser', models.ForeignKey(db_column='touserid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'message',
            },
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('localpathstr', models.TextField(blank=True)),
                ('remotepathstr', models.TextField(blank=True)),
                ('skip', models.BooleanField()),
                ('is_movie', models.BooleanField(db_column='ismovie')),
                ('tvdb_id', models.TextField(blank=True, null=True)),
                ('server', models.TextField()),
                ('defaultsearchstr', models.TextField(blank=True, null=True)),
                ('imdb_id', models.TextField(blank=True, null=True)),
                ('override_display_name', models.TextField(blank=True, db_column='display_name', null=True)),
                ('lastCreatedFileDate', models.DateTimeField(blank=True, db_column='lastcreatedfiledate', null=True)),
                ('defaultScraper', models.ForeignKey(blank=True, db_column='defaultscraperid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.FilenameScrapeFormat')),
            ],
            options={
                'db_table': 'path',
            },
        ),
        migrations.CreateModel(
            name='PosterFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('dateedited', models.DateTimeField(blank=True, db_column='dateedited')),
                ('image', models.TextField(blank=True)),
                ('plot', models.TextField(blank=True)),
                ('extendedplot', models.TextField(blank=True)),
                ('genre', models.TextField(blank=True)),
                ('actors', models.TextField(blank=True)),
                ('writer', models.TextField(blank=True)),
                ('director', models.TextField(blank=True)),
                ('episodename', models.TextField(blank=True, null=True)),
                ('rated', models.TextField(blank=True, null=True)),
                ('rating', models.TextField(blank=True, null=True)),
                ('file', models.ForeignKey(blank=True, db_column='fileid', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='_posterfile', to='mediaviewer.File')),
                ('path', models.ForeignKey(blank=True, db_column='pathid', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='_posterfile', to='mediaviewer.Path')),
            ],
            options={
                'db_table': 'posterfile',
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('dateedited', models.DateTimeField(blank=True, db_column='dateedited')),
                ('name', models.TextField(blank=True)),
                ('done', models.BooleanField()),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'request',
            },
        ),
        migrations.CreateModel(
            name='RequestVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('request', models.ForeignKey(db_column='requestid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.Request')),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'requestvote',
            },
        ),
        migrations.CreateModel(
            name='SiteGreeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('greeting', models.TextField(blank=True, db_column='greeting')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sitegreeting',
            },
        ),
        migrations.CreateModel(
            name='UserComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('dateedited', models.DateTimeField(blank=True, db_column='dateedited')),
                ('comment', models.TextField(blank=True)),
                ('viewed', models.BooleanField(db_column='viewed')),
                ('file', models.ForeignKey(db_column='fileid', on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.File')),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'usercomment',
            },
        ),
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datecreated', models.DateTimeField(blank=True, db_column='datecreated')),
                ('dateedited', models.DateTimeField(blank=True, db_column='dateedited')),
                ('ip_format', models.TextField(db_column='ip_format')),
                ('can_download', models.BooleanField(db_column='can_download')),
                ('site_theme', models.TextField(db_column='site_theme')),
                ('default_sort', models.TextField(db_column='default_sort')),
                ('auto_download', models.BooleanField(db_column='auto_download', default=False)),
                ('force_password_change', models.BooleanField(db_column='force_password_change', default=False)),
                ('can_login', models.BooleanField(db_column='can_login', default=True)),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'usersettings',
            },
        ),
        migrations.CreateModel(
            name='VideoProgress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.TextField(db_column='filename')),
                ('offset', models.DecimalField(decimal_places=3, max_digits=9)),
                ('date_edited', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'videoprogress',
            },
        ),
        migrations.CreateModel(
            name='WaiterStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_column='status')),
                ('failureReason', models.TextField(db_column='failurereason')),
                ('datecreated', models.DateTimeField(db_column='datecreated')),
            ],
            options={
                'db_table': 'waiterstatus',
            },
        ),
        migrations.AddField(
            model_name='file',
            name='filenamescrapeformat',
            field=models.ForeignKey(blank=True, db_column='filenamescrapeformatid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.FilenameScrapeFormat'),
        ),
        migrations.AddField(
            model_name='file',
            name='path',
            field=models.ForeignKey(blank=True, db_column='pathid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.Path'),
        ),
        migrations.AddField(
            model_name='error',
            name='file',
            field=models.ForeignKey(blank=True, db_column='fileid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.File'),
        ),
        migrations.AddField(
            model_name='error',
            name='path',
            field=models.ForeignKey(blank=True, db_column='pathid', null=True, on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.Path'),
        ),
        migrations.AddField(
            model_name='downloadtoken',
            name='file',
            field=models.ForeignKey(blank=True, db_column='fileid', on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.File'),
        ),
        migrations.AddField(
            model_name='downloadtoken',
            name='user',
            field=models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='downloadclick',
            name='downloadtoken',
            field=models.ForeignKey(db_column='downloadtokenid', on_delete=django.db.models.deletion.CASCADE, to='mediaviewer.DownloadToken'),
        ),
        migrations.AddField(
            model_name='downloadclick',
            name='user',
            field=models.ForeignKey(db_column='userid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
