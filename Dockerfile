FROM dddecaf/postgres-base:master

ENV APP_USER=giraffe

ARG UID=1000
ARG GID=1000

ARG CWD=/app

ENV PYTHONPATH=${CWD}/src

RUN addgroup -g "${GID}" -S "${APP_USER}" && \
    adduser -u "${UID}" -G "${APP_USER}" -S "${APP_USER}"

WORKDIR "${CWD}"

COPY requirements ./requirements

RUN pip-sync requirements/requirements.txt

COPY . "${CWD}/"

RUN chown -R "${APP_USER}:${APP_USER}" "${CWD}"
