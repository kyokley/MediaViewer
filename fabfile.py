from fabric import colors
from fabric import api as fab
from fabric import decorators
from fabric.contrib import files

import os, getpass

fab.env.colors = True

OS_COMMANDS = ('sudo apt-get install aptitude',
               'sudo aptitude update',
               'sudo aptitude install python-dev',
               'sudo aptitude install python-pip',
               'sudo aptitude install python-virtualenv supervisor uwsgi uwsgi-plugin-python nginx',
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
plugins = python
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

    ssl_protocols        TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers          HIGH:!aNULL:!MD5;
	ssl_prefer_server_ciphers on;

    # Django media
    location /media  {{
        alias {installDir}/mediaviewer/static/media;  # your Django project's media files - amend as required
        expires 1y;
    }}

    location /static {{
        alias {installDir}/mediaviewer/static; # your Django project's static files - amend as required
        expires 1d;
    }}

    # Finally, send all non-media requests to the Django server.
    location /mediaviewer{{
        uwsgi_pass  django;
        include     {installDir}/server/uwsgi_params; # the uwsgi_params file you installed
    }}

    location /admin{{
        uwsgi_pass  django;
        include     {installDir}/server/uwsgi_params; # the uwsgi_params file you installed
    }}

    location /static/admin/ {{
        # this changes depending on your python version
        root {venv_location}/lib/python2.7/site-packages/django/contrib/admin/;
        expires 1y;
    }}
}}
'''

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

def deactivate_venv():
    fab.local('deactivate')

def run_command_list(commands, values=None):
    for command in commands:
        if values:
            fab.local(command.format(**values))
        else:
            fab.local(command)

def write_sudo_file(filename, text):
    files.append(filename, text, use_sudo=True)

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

    uwsgiText = uwsgiTextTemplate.format(**values)
    if os.path.exists(values['uwsgiConfLocation']):
        fab.local('sudo rm %s' % values['uwsgiConfLocation'])
    write_sudo_file(values['uwsgiConfLocation'], uwsgiText)

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

    fab.local('sudo supervisorctl update')
    fab.local('sudo supervisorctl restart %s' % values['programName'])
    fab.local('sudo service nginx restart')
