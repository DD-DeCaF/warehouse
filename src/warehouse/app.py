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

"""Expose the main Flask application."""

import logging
import logging.config

from flask import Flask, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
from werkzeug.middleware.proxy_fix import ProxyFix

from warehouse import errorhandlers, jwt
from warehouse.settings import current_settings


app = Flask(__name__)
app.config.from_object(current_settings())
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app, name="warehouse")
basic_auth = BasicAuth(app)


def init_app(application):
    """Initialize the main app with config information and routes."""
    from warehouse import models, resources

    logging.config.dictConfig(application.config["LOGGING"])
    application.wsgi_app = ProxyFix(application.wsgi_app)

    # Configure Sentry
    if application.config["SENTRY_DSN"]:
        sentry = Sentry(
            dsn=application.config["SENTRY_DSN"], logging=True, level=logging.WARNING
        )
        sentry.init_app(application)

    # Add JWT middleware
    jwt.init_app(application)

    # Add custom error handlers
    errorhandlers.init_app(application)

    # Add routes and resources
    resources.init_app(application)

    # Add the flask-admin interface
    @application.before_request
    def restrict_admin():
        if request.path.startswith(admin.url) and not basic_auth.authenticate():
            return basic_auth.challenge()

    admin.add_view(ModelView(models.Organism, db.session))
    admin.add_view(ModelView(models.Strain, db.session))
    admin.add_view(ModelView(models.Experiment, db.session))
    admin.add_view(ModelView(models.Medium, db.session))
    admin.add_view(ModelView(models.MediumCompound, db.session))
    admin.add_view(ModelView(models.Condition, db.session))
    admin.add_view(ModelView(models.Sample, db.session))
    admin.add_view(ModelView(models.Fluxomics, db.session))
    admin.add_view(ModelView(models.Metabolomics, db.session))
    admin.add_view(ModelView(models.UptakeSecretionRates, db.session))
    admin.add_view(ModelView(models.MolarYields, db.session))
    admin.add_view(ModelView(models.Growth, db.session))

    # Add CORS information for all resources.
    CORS(application)
