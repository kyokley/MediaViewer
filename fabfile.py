from fabric import colors
from fabric import api as fab
from fabric import decorators
from fabric.contrib import files

import os, getpass

fab.env.colors = True

OS_COMMANDS = ('sudo apt-get install aptitude',
               'sudo aptitude update',
               'sudo aptitude install python-dev -y',
               'sudo aptitude install python-pip -y',
               'sudo aptitude install python-virtualenv supervisor uwsgi uwsgi-plugin-python nginx postgresql postgresql-server-dev-9.5 -y',
               'sudo aptitude install libffi-dev postfix -y',
               )

NODE_COMMANDS = (
                 'sudo aptitude install npm',
                 )

certCommands = (
'openssl genrsa -aes256 -out {installDir}/server/server.key 4096',
'openssl req -new -key {installDir}/server/server.key -out {installDir}/server/server.csr',
'cp {installDir}/server/server.key {installDir}/server/server.key.org',
'openssl rsa -in {installDir}/server/server.key.org -out {installDir}/server/server.key',
'openssl x509 -req -days 365 -in {installDir}/server/server.csr -signkey {installDir}/server/server.key -out {installDir}/server/server.crt',
)

supervisorTextTemplate = '''
[program:{programName}]
command=uwsgi --ini {uwsgiConfLocation}
autostart=true
autorestart=true
stdout_logfile=/var/log/{programName}.out.log
redirect_stderr=true
user={user}
stopsignal=QUIT
environment=LANG=en_US.UTF-8, LC_ALL=en_US.UTF-8, LC_LANG=en_US.UTF-8
stdout_logfile_maxbytes=500000
stdout_logfile_backups=10
'''

uwsgiTextTemplate = '''
[uwsgi]
socket = /tmp/{programName}.sock
chdir = {installDir}
virtualenv = {venv_location}
env = DJANGO_SETTINGS_MODULE=mysite.settings
home = {venv_location}
uid = {user}
gid = {user}
processes = 8
threads = 2
module = django.core.handlers.wsgi:WSGIHandler()
chmod-socket = 666
'''

nginxTextTemplate = '''
upstream django {{
     server unix:///tmp/{programName}.sock; # for a file socket
}}

# configuration of the server
server {{
    # the port your site will be served on
    listen      {port};
    # the domain name it will serve for
    server_name {serverName};

    rewrite ^(.*) https://$host:{securePort}$1 permanent;
}}

server {{
    listen {apiPort};
    server_name {serverName};
    location /mediaviewer/api{{
        uwsgi_pass  django;
        include     {installDir}/server/uwsgi_params; # the uwsgi_params file you installed
    }}
}}

server {{
    listen {securePort};
    server_name {serverName};

    ssl on;
    ssl_certificate {installDir}/server/server.crt;
    ssl_certificate_key {installDir}/server/server.key;

    ssl_session_timeout 5m;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers "EECDH+ECDSA+AESGCM:EECDH+aRSA+AESGCM:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA256:EECDH+ECDSA+SHA384:EECDH+ECDSA+SHA256:EECDH+aRSA+SHA384:EDH+aRSA+AESGCM:EDH+aRSA+SHA256:EDH+aRSA:EECDH:!aNULL:!eNULL:!MEDIUM:!LOW:!3DES:!MD5:!EXP:!PSK:!SRP:!DSS:!RC4:!SEED";
    ssl_prefer_server_ciphers on;

    # Django media
    location /media  {{
        alias {installDir}/mediaviewer/static/media;
        expires 1y;
    }}

    location /static {{
        alias {installDir}/static;
        expires 1d;
    }}

    # Finally, send all non-media requests to the Django server.
    location /mediaviewer{{
        uwsgi_pass  django;
        include     {installDir}/server/uwsgi_params;
    }}

    location /admin{{
        uwsgi_pass  django;
        include     {installDir}/server/uwsgi_params;
    }}

    location /static/admin/ {{
        # this changes depending on your python version
        root {venv_location}/lib/python2.7/site-packages/django/contrib/admin/;
        expires 1y;
    }}

    location /static/rest_framework/ {{
        # this changes depending on your python version
        root {venv_location}/local/lib/python2.7/site-packages/rest_framework;
        expires 1y;
    }}

}}
'''

dailyTemplate = '''#!/bin/bash

echo "Starting daily cleanup `date`"
psql -d autodl -f {installDir}/daily.sql
echo "Ending daily cleanup `date`"
'''

virtualenvPthTemplate = '{installDir}'

def create_venv(venv_home, venv_name):
    venv_location = os.path.join(venv_home, venv_name)
    fab.local('virtualenv -p python2.7 %s' % venv_location)
    return venv_location

def get_venv_prefix(venv_location):
    return '/bin/bash %s' % os.path.join(venv_location, 'bin', 'activate')

def install_venv_requirements(installDir, venv_location, prefix):
    fab.local('%s && %s install -r %s' % (prefix,
                                          os.path.join(venv_location, 'bin', 'pip'),
                                          os.path.join(installDir, 'requirements.txt')))


def run_command_list(commands, values=None):
    for command in commands:
        if values:
            fab.local(command.format(**values))
        else:
            fab.local(command)

def write_file(filename, text, use_sudo=False):
    files.append(filename, text, use_sudo=use_sudo)

def write_sudo_file(filename, text):
    write_file(filename, text, use_sudo=True)

def add_cronjob(text):
    with fab.warn_only():
        fab.local('crontab -l > /tmp/crondump')
        fab.local('echo "%s 2> /dev/null" >> /tmp/crondump' % text)
        fab.local('crontab /tmp/crondump')

@fab.task
@decorators.hosts(['localhost'])
def update_bower():
    run_command_list(NODE_COMMANDS)
    fab.local('sudo npm install -g bower')
    fab.local('python manage.py bower install')

@fab.task
@decorators.hosts(['localhost'])
def install():
    user = getpass.getuser()
    installDir = os.getcwd()

    run_command_list(OS_COMMANDS)

    venv_home = fab.prompt(colors.cyan('Specify directory where you want the '
                                       'virtual environment to be created:'),
                           default='%s/virtualenvs' % os.path.expanduser('~'))
    venv_name = fab.prompt(colors.cyan('Specify the name of the environment'),
                           default='mediaviewer')
    venv_location = create_venv(venv_home, venv_name)
    prefix = get_venv_prefix(venv_location)
    install_venv_requirements(installDir, venv_location, prefix)

    programName = fab.prompt(colors.cyan('Specify program name'), default='mediaviewer')
    serverName = fab.prompt(colors.cyan('Specify server IP address or FQDN'), default='127.0.0.1')
    port = fab.prompt(colors.cyan('Specify port to run application on'), default='8000')
    securePort = fab.prompt(colors.cyan('Specify secure port to run application on'), default='8001')
    apiPort = fab.prompt(colors.cyan('Specify api port to run application on'), default='8002')
    values = {'programName': programName,
              'user': user,
              'venv_location': venv_location,
              'installDir': installDir,
              'uwsgiConfLocation': os.path.join(installDir, 'uwsgi.ini'),
              'port': port,
              'securePort': securePort,
              'apiPort': apiPort,
              'serverName': serverName,
              }
    run_command_list(certCommands, values=values)

    virtualenvPthText = virtualenvPthTemplate.format(**values)
    write_file(os.path.join(venv_location,
                            'lib',
                            'python2.7',
                            'site-packages',
                            'mediaviewer.pth'), virtualenvPthText)

    uwsgiText = uwsgiTextTemplate.format(**values)
    if os.path.exists(values['uwsgiConfLocation']):
        fab.local('sudo rm %s' % values['uwsgiConfLocation'])
    write_sudo_file(values['uwsgiConfLocation'], uwsgiText)

    dailyBash = dailyTemplate.format(**values)
    dailyBashPath = os.path.join(installDir, 'daily.sh')
    write_file(dailyBashPath, dailyBash)
    fab.local('chmod a+x %s' % dailyBashPath)
    add_cronjob('@daily {installDir}/daily.sh'.format(**values))

    supervisorText = supervisorTextTemplate.format(**values)
    supervisorPath = os.path.join('/etc/supervisor/conf.d', '%s.conf' % values['programName'])

    if os.path.exists(supervisorPath):
        fab.local('sudo rm %s' % supervisorPath)
    write_sudo_file(supervisorPath, supervisorText)

    nginxText = nginxTextTemplate.format(**values)
    nginxPath = os.path.join('/etc/nginx/sites-enabled/%s.conf' % values['programName'])
    if os.path.exists(nginxPath):
        fab.local('sudo rm %s' % nginxPath)
    write_sudo_file(nginxPath, nginxText)

    fab.local('sudo systemctl start supervisor')
    fab.local('sudo supervisorctl update')
    fab.local('sudo supervisorctl restart %s' % values['programName'])
    fab.local('sudo service nginx restart')
