FROM python:3.6-slim

MAINTAINER Kevin Yokley

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG REQS=--no-dev

# Install required packages and remove the apt packages cache when done.
RUN apt-get update && \
    apt-get install -y g++ \
                       git \
                       curl \
                       yarn \
                       make \
                       gnupg

RUN python -m venv /venv

RUN echo '{ "allow_root": true }' > /root/.bowerrc
RUN echo 'alias venv="source /venv/bin/activate"' >> /root/.bashrc

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

COPY poetry.lock /code/poetry.lock
COPY pyproject.toml /code/pyproject.toml

RUN /bin/bash -c "source /venv/bin/activate && \
                  cd /code && \
                  /root/.poetry/bin/poetry install ${REQS}"

COPY . /code
WORKDIR /code

#EXPOSE 8000 8001 8002
#ENTRYPOINT ["supervisord", "-n", "-c", "/etc/supervisor.d/supervisor.conf"]
CMD uwsgi --ini /home/docker/code/uwsgi/uwsi.conf
