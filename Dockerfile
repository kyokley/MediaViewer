FROM alpine:latest

MAINTAINER Kevin Yokley

ENV HOME /home/docker
RUN mkdir $HOME
RUN addgroup -S docker && \
    adduser -S docker -g docker \
    && chown -R docker:docker $HOME

# Install required packages and remove the apt packages cache when done.
RUN apk add --no-cache --virtual .build-deps \
    linux-headers \
    g++ \
    git \
    python \
    python-dev \
    py-virtualenv \
    py2-pip \
    supervisor \
    postgresql \
    postgresql-dev \
    nodejs

RUN virtualenv -p python /virtualenv

COPY requirements.txt /home/docker/code/app/
RUN /virtualenv/bin/pip install -r /home/docker/code/app/requirements.txt

# add (the rest of) our code
COPY . $HOME/code/

#RUN ln -s /home/docker/code/nginx/nginx-mediaviewer.conf /etc/nginx/conf.d/mediaviewer.conf
#RUN ln -s /home/docker/code/supervisor/supervisor.conf /etc/supervisor.d/supervisor.conf

RUN rm -f $HOME/code/mysite/local_settings.py && \
    cp $HOME/code/mysite/docker_settings.py $HOME/code/mysite/local_settings.py

WORKDIR $HOME/code
#USER docker

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD /bin/sh
