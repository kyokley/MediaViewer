FROM alpine:latest

MAINTAINER Kevin Yokley

# Install required packages and remove the apt packages cache when done.

RUN apk update
RUN apk add --no-cache --virtual .build-deps \
    linux-headers \
    g++ \
	git \
	python3 \
	python3-dev \
	nginx \
	supervisor \
    nodejs && \
	pip3 install -U pip setuptools

RUN pip3 install uwsgi django

# setup all the configfiles
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
COPY nginx-app.conf /etc/nginx/sites-available/default
COPY supervisor-app.conf /etc/supervisor/conf.d/

# COPY requirements.txt and RUN pip install BEFORE adding the rest of your code, this will cause Docker's caching mechanism
# to prevent re-installing (all your) dependencies when you made a change a line or two in your app.

COPY requirements.txt /home/docker/code/app/
RUN pip3 install -r /home/docker/code/app/requirements.txt

# add (the rest of) our code
COPY . /home/docker/code/

EXPOSE 8000 8001 8002
CMD ["supervisord", "-n"]
