ARG BASE_IMAGE=python:3.12-slim

FROM ${BASE_IMAGE} AS static-builder
WORKDIR /code

RUN apt-get update && apt-get install -y \
        npm \
        make

RUN mkdir /code/static
COPY package.json package-lock.json /code/
RUN npm install

FROM ${BASE_IMAGE} AS base
ARG UID=1000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /www
WORKDIR /logs

RUN groupadd -g ${UID} -r user && \
        useradd --create-home --system --uid ${UID} --gid user user && \
        chown -R user:user /logs /www && \
        chmod 777 -R /www

RUN pip install -U pip

ENV POETRY_VENV=/poetry_venv
RUN python3 -m venv $POETRY_VENV

ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH:$POETRY_VENV/bin"

# Install required packages and remove the apt packages cache when done.
RUN apt-get update && apt-get install -y \
        gnupg \
        g++ \
        git \
        apt-transport-https \
        ncurses-dev \
        libpq-dev \
        make

COPY ./pdbrc.py /root/.pdbrc.py

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN $POETRY_VENV/bin/pip install poetry && $POETRY_VENV/bin/poetry install --without dev


# ********************* Begin Prod Image ******************
FROM base AS prod
COPY --from=static-builder /code/node_modules /node/node_modules
COPY . /code
RUN chown user:user -R /code && \
        python manage.py collectstatic --no-input
USER user
CMD gunicorn mysite.wsgi


# ********************* Begin Dev Image ******************
FROM base AS dev-root
RUN $POETRY_VENV/bin/poetry install
COPY --from=static-builder /code/node_modules /node/node_modules

FROM dev-root AS dev
USER user
