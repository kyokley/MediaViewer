FROM alpine:latest

MAINTAINER Kevin Yokley

ENV HOME /home/docker
RUN mkdir $HOME
RUN addgroup -S docker && \
    adduser -S docker -g docker \
    && chown -R docker:docker $HOME

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
    postgresql \
    postgresql-dev \
    nodejs && \
    pip3 install -U pip \
                    setuptools

RUN pip3 install uwsgi django

# setup all the configfiles
#VOLUME nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

#VOLUME /etc/supervisor.d/supervisor.conf
#RUN mkdir /etc/supervisor.d
#RUN ln -s /home/docker/code/supervisor/supervisor.conf /etc/supervisor.d/supervisor.conf

# COPY requirements.txt and RUN pip install BEFORE adding the rest of your code, this will cause Docker's caching mechanism
# to prevent re-installing (all your) dependencies when you made a change a line or two in your app.

COPY requirements.txt /home/docker/code/app/
RUN pip3 install -r /home/docker/code/app/requirements.txt

# add (the rest of) our code
COPY . $HOME/code/

RUN ln -s /home/docker/code/nginx/nginx-mediaviewer.conf /etc/nginx/conf.d/mediaviewer.conf
#RUN ln -s /home/docker/code/supervisor/supervisor.conf /etc/supervisor.d/supervisor.conf

RUN rm -f $HOME/code/mysite/local_settings.py && \
    cp $HOME/code/mysite/docker_settings.py $HOME/code/mysite/local_settings.py


WORKDIR $HOME
#USER docker

EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD /bin/sh
