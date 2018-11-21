FROM dddecaf/wsgi-base:master

ENV APP_USER=giraffe

ARG UID=1000
ARG GID=1000

ARG CWD=/app

ENV PYTHONPATH=${CWD}/src

RUN addgroup -g "${GID}" -S "${APP_USER}" && \
    adduser -u "${UID}" -G "${APP_USER}" -S "${APP_USER}"

WORKDIR "${CWD}"

# postgresql-dev and g++ are required to build psycopg2
RUN apk add --update --no-cache postgresql-dev g++

COPY requirements.in dev-requirements.in ./

# `wsgi-requirements.txt` comes from the parent image and needs to be part of
# the `pip-sync` command otherwise those dependencies are removed.
RUN set -eux \
    && pip-compile --generate-hashes \
        --output-file dev-requirements.txt dev-requirements.in \
    && pip-compile --generate-hashes \
        --output-file requirements.txt requirements.in \
    && pip-sync /opt/wsgi-requirements.txt \
        dev-requirements.txt \
        requirements.txt \
    && rm -rf /root/.cache/pip

COPY . "${CWD}/"

RUN chown -R "${APP_USER}:${APP_USER}" "${CWD}"
