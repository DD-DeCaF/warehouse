FROM python:3.6-alpine3.7

ENV PYTHONUNBUFFERED=1

ENV APP_USER=giraffe

ARG UID=1000
ARG GID=1000

ARG CWD=/app

ENV PYTHONPATH=${CWD}/src

ARG PIPENV_FLAGS="--dev"

RUN addgroup -g "${GID}" -S "${APP_USER}" && \
    adduser -u "${UID}" -G "${APP_USER}" -S "${APP_USER}"

RUN apk add --update --no-cache openssl ca-certificates

WORKDIR "${CWD}"

COPY . "${CWD}/"

# `g++` is required for building `gevent` but all build dependencies are
# later removed again to reduce the layer size.
# The symlink is a temporary workaround for a bug in pipenv.
# Still present as of pipenv==11.9.0.
RUN set -x \
    && ln -sf /usr/local/bin/python /bin/python \
    && apk add postgresql-libs \
    && apk add --no-cache --virtual .build-deps g++ git musl-dev postgresql-dev \
    && pip install --upgrade pip setuptools wheel pipenv==11.10.0 \
    && pipenv install --system ${PIPENV_FLAGS} \
    && rm -rf /root/.cache/pip \
    && apk del .build-deps

RUN chown -R "${APP_USER}:${APP_USER}" "${CWD}"
