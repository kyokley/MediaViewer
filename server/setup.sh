#!/bin/bash

sudo aptitude install nginx

sudo ln -s /home/yokley/workspace/djangoApp/server/mediaviewer.conf /etc/nginx/sites-available/mediaviewer.conf
sudo ln -s /etc/nginx/sites-available/mediaviewer.conf /etc/nginx/sites-enabled/mediaviewer.conf

sudo service nginx reload
