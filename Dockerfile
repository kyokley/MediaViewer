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
    nodejs \
    npm
RUN npm install -g bower

ARG REQS=base

RUN virtualenv -p python /venv

COPY ./requirements /home/docker/code/requirements
RUN /venv/bin/pip install -r /home/docker/code/requirements/${REQS}_requirements.txt

# add (the rest of) our code
COPY . $HOME/code/

RUN addgroup -S docker && \
    adduser -S docker -g docker \
    && chown -R docker:docker $HOME
USER docker

RUN rm -f $HOME/code/mysite/local_settings.py && \
    cp $HOME/code/configs/docker_settings.py $HOME/code/mysite/local_settings.py

WORKDIR $HOME/code

COPY ./package.json /home/docker/code/package.json
RUN /venv/bin/python $HOME/code/manage.py bower install

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD /bin/sh
