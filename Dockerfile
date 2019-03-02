FROM python:3.6-slim

MAINTAINER Kevin Yokley

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG REQS=--no-dev

# Install required packages and remove the apt packages cache when done.
RUN apt-get update && apt-get install -y \
        curl \
        gnupg \
        g++ \
        git \
        apt-transport-https \
        ncurses-dev \
        make

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -

RUN apt-get update && apt-get install -y yarn nodejs

RUN python -m venv /venv

RUN echo 'alias venv="source /venv/bin/activate"' >> /root/.bashrc
RUN echo 'export PATH=$PATH:/root/.poetry/bin' >> /root/.bashrc

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

COPY package.json /node/package.json

COPY poetry.lock /code/poetry.lock
COPY pyproject.toml /code/pyproject.toml

RUN /bin/bash -c "source /venv/bin/activate && \
                  cd /code && \
                  pip install --upgrade pip && \
                  /root/.poetry/bin/poetry install -vvv ${REQS}"

RUN cd /node && yarn install && rsync -ruv /node/node_modules/* /code/static/

COPY . /code
WORKDIR /code

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD uwsgi --ini /home/docker/code/uwsgi/uwsi.conf
