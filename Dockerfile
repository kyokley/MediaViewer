ARG BASE_IMAGE=python:3.12-slim

FROM ${BASE_IMAGE} AS base-image
RUN apt-get update

FROM node:alpine3.20 AS static-builder
WORKDIR /code/static

COPY package.json package-lock.json /code/
RUN npm install

FROM base-image AS base
ARG UID=1000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /www
WORKDIR /logs

RUN groupadd -g ${UID} -r user && \
        useradd --create-home --system --uid ${UID} --gid user user && \
        chown -R user:user /logs /www && \
        chmod 777 -R /www

RUN pip install -U pip uv

ENV UV_PROJECT_DIR=/mv
ENV VIRTUAL_ENV=${UV_PROJECT_DIR}/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv venv --seed ${VIRTUAL_ENV}

# Install required packages and remove the apt packages cache when done.
RUN apt-get install -y \
        gnupg \
        g++ \
        git \
        apt-transport-https \
        ncurses-dev \
        libpq-dev \
        make

COPY ./pdbrc.py /root/.pdbrc.py

COPY uv.lock pyproject.toml ${UV_PROJECT_DIR}

RUN uv sync --no-dev --project ${VIRTUAL_ENV}


# ********************* Begin Prod Image ******************
FROM base AS prod
ARG MV_LOG_DIR=/logs

COPY --from=static-builder /code/node_modules /node/node_modules
COPY . /code

WORKDIR /code
RUN SKIP_LOADING_TVDB_CONFIG=1 python manage.py collectstatic --no-input && \
        chown user:user -R /code

USER user
CMD ["gunicorn", "mysite.wsgi"]


# ********************* Begin Dev Image ******************
FROM base AS dev-root
WORKDIR /venv
RUN uv sync --project ${VIRTUAL_ENV}

WORKDIR /code

COPY --from=static-builder /code/node_modules /node/node_modules

FROM dev-root AS dev
USER user
