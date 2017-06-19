FROM alpine:latest

MAINTAINER Kevin Yokley

ENV HOME /home/docker
RUN mkdir $HOME

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

RUN virtualenv -p python $HOME/virtualenv

COPY requirements.txt /home/docker/code/app/
RUN $HOME/virtualenv/bin/pip install -r /home/docker/code/app/requirements.txt

# add (the rest of) our code
COPY . $HOME/code/

RUN addgroup -S docker && \
    adduser -S docker -g docker \
    && chown -R docker:docker $HOME
USER docker

RUN rm -f $HOME/code/mysite/local_settings.py && \
    cp $HOME/code/configs/docker_settings.py $HOME/code/mysite/local_settings.py

WORKDIR $HOME/code

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD /bin/sh
