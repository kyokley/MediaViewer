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

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install -U pip

ENV POETRY_VENV=/poetry_venv
RUN python3 -m venv $POETRY_VENV

ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH:$POETRY_VENV/bin"

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

COPY ./pdbrc.py /root/.pdbrc.py

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN $POETRY_VENV/bin/pip install poetry && $POETRY_VENV/bin/poetry install --without dev


# ********************* Begin Prod Image ******************
FROM base AS prod
COPY --from=static-builder /code/node_modules /node/node_modules
COPY . /code
RUN python manage.py collectstatic --no-input
CMD gunicorn mysite.wsgi


# ********************* Begin Dev Image ******************
FROM base AS dev
RUN $POETRY_VENV/bin/poetry install
COPY --from=static-builder /code/node_modules /node/node_modules
