# warehouse

![master Branch](https://img.shields.io/badge/branch-master-blue.svg)
[![master Build Status](https://travis-ci.org/DD-DeCaF/warehouse.svg?branch=master)](https://travis-ci.org/DD-DeCaF/warehouse)
[![master Codecov](https://codecov.io/gh/DD-DeCaF/warehouse/branch/master/graph/badge.svg)](https://codecov.io/gh/DD-DeCaF/warehouse/branch/master)

![devel Branch](https://img.shields.io/badge/branch-devel-blue.svg)
[![devel Build Status](https://travis-ci.org/DD-DeCaF/warehouse.svg?branch=devel)](https://travis-ci.org/DD-DeCaF/warehouse)
[![devel Codecov](https://codecov.io/gh/DD-DeCaF/warehouse/branch/devel/graph/badge.svg)](https://codecov.io/gh/DD-DeCaF/warehouse/branch/devel)


## Development

Run `make setup` first when initializing the project for the first time. Type
`make` to see all commands.

## Testing

To run the tests locally, run the following commands

To start the containers:
```
make start
```

To run the database migrations for the clean database:
```
make upgrade
```

To test locally (will only work correctly if all the commands above are executed):
```
make test
```

To stop and delete containers (will not delete the database)
```
make clean
```

### Environment

Specify environment variables in a `.env` file. See `docker-compose.yml` for the
possible variables and their default values.

* Set `ENVIRONMENT` to either
  * `development`,
  * `testing`, or
  * `production`.
* `SECRET_KEY` Flask secret key. Will be randomly generated in development and testing environments.
* `SENTRY_DSN` DSN for reporting exceptions to
  [Sentry](https://docs.sentry.io/clients/python/integrations/flask/).
* `ALLOWED_ORIGINS`: Comma-seperated list of CORS allowed origins.
* `FLASK_APP`: `src/warehouse/wsgi.py`

### Updating Python dependencies

To compile a new requirements file and then re-build the service with the new requirements, run:

    make pip-compile build
