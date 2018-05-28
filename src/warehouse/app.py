# Copyright (c) 2018, Novo Nordisk Foundation Center for Biosustainability,
# Technical University of Denmark.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Expose the main Flask-RESTPlus application."""

import logging
import logging.config
import os
import requests

from flask import Flask
from flask_cors import CORS
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from raven.contrib.flask import Sentry


def fetch_jwt_public_key():
    return requests.get(os.environ['IAM_KEYS']).json()["keys"][0]["n"]


app = Flask(__name__)
if os.environ["ENVIRONMENT"] == "production":
    from warehouse.settings import Production

    app.config.from_object(Production())
    app.config['JWT_PUBLIC_KEY'] = fetch_jwt_public_key()
elif os.environ["ENVIRONMENT"] == "testing":
    from warehouse.settings import Testing

    app.config.from_object(Testing())
    app.testing = True
else:
    from warehouse.settings import Development

    app.config.from_object(Development())
jwt = JWTManager(app)
api = Api(
    title="warehouse",
    version="0.1.0",
    description="The storage for the experimental data used for modeling: omics, strains, media etc",
)
jwt._set_error_handler_callbacks(api)  # until https://github.com/noirbizarre/flask-restplus/issues/340 is fixed
db = SQLAlchemy(app)
migrate = Migrate(app, db)


def init_app(application, interface):
    """Initialize the main app with config information and routes."""
    # Configure logging
    # The flask logger, when created, disables existing loggers. The following
    # statement ensures the flask logger is created, so that it doesn't disable
    # our loggers later when it is first accessed.
    application.logger
    logging.config.dictConfig(application.config['LOGGING'])

    # Configure Sentry
    if application.config['SENTRY_DSN']:
        sentry = Sentry(dsn=application.config['SENTRY_DSN'], logging=True,
                        level=logging.WARNING)
        sentry.init_app(application)

    # Add routes and resources.
    from warehouse import resources, models
    interface.init_app(application)

    # Add CORS information for all resources.
    CORS(application)
