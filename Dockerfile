FROM python:3.6-alpine

MAINTAINER Kevin Yokley

# Install required packages and remove the apt packages cache when done.
RUN apk add --no-cache --virtual .build-deps \
    linux-headers \
    g++ \
    git \
    supervisor \
    postgresql \
    postgresql-dev \
    python3-dev \
    nodejs \
    npm
RUN npm install -g bower

ARG REQS=base

RUN python -m venv /venv

COPY ./requirements /home/docker/code/requirements
RUN /venv/bin/pip install -U pip \
 && /venv/bin/pip install -r /home/docker/code/requirements/${REQS}_requirements.txt

# add (the rest of) our code
COPY . /code

RUN addgroup -S docker && \
    adduser -S docker -g docker \
    && chown -R docker:docker /code
USER docker

RUN cp -f /code/configs/docker_settings.py /code/mysite/local_settings.py

WORKDIR /code

COPY ./package.json /code/package.json
RUN /venv/bin/python manage.py bower install

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD /bin/sh
