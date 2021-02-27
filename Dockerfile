ARG BASE_IMAGE=python:3.8-slim

FROM ${BASE_IMAGE} AS static-builder
WORKDIR /code

RUN apt-get update && apt-get install -y \
        npm \
        make

RUN npm install -g yarn
RUN mkdir /code/static
COPY package.json /code/package.json
RUN yarn install

FROM ${BASE_IMAGE} AS base

MAINTAINER Kevin Yokley

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Add virtualenv to bash prompt
RUN echo 'if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then \n\
              _OLD_VIRTUAL_PS1="${PS1:-}" \n\
              if [ "x(venv) " != x ] ; then \n\
                PS1="(venv) ${PS1:-}" \n\
              else \n\
              if [ "`basename \"$VIRTUAL_ENV\"`" = "__" ] ; then \n\
                  # special case for Aspen magic directories \n\
                  # see http://www.zetadev.com/software/aspen/ \n\
                  PS1="[`basename \`dirname \"$VIRTUAL_ENV\"\``] $PS1" \n\
              else \n\
                  PS1="(`basename \"$VIRTUAL_ENV\"`)$PS1" \n\
              fi \n\
              fi \n\
              export PS1 \n\
          fi' >> ~/.bashrc

# Install required packages and remove the apt packages cache when done.
RUN apt-get update && apt-get install -y \
        gnupg \
        g++ \
        git \
        apt-transport-https \
        ncurses-dev \
        libpq-dev \
        make

RUN pip install -U pip poetry

WORKDIR /code
COPY poetry.lock pyproject.toml /code

RUN poetry install --no-dev

COPY --from=static-builder /code/node_modules /node/node_modules

# ********************* Begin Prod Image ******************
FROM base AS prod
COPY . /code
CMD uwsgi --ini /code/uwsgi/uwsi.conf


# ********************* Begin Dev Image ******************
FROM base AS dev
RUN poetry install
