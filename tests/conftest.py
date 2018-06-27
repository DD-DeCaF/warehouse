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

"""Provide session level fixtures."""

import pytest
from flask_jwt_extended import create_access_token

from warehouse.app import api
from warehouse.app import app as app_
from warehouse.app import init_app, jwt


PROJECTS1 = [1, 2]
PROJECTS2 = [4]


@pytest.fixture(scope="session")
def app():
    """Provide an initialized Flask for use in certain test cases."""
    init_app(app_, api)
    return app_


@pytest.fixture(scope="session")
def client(app):
    """Provide a Flask test client to be used by almost all test cases."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="session")
def tokens(app):
    """Provides two tokens with different claims to test the permissions"""
    @jwt.user_claims_loader
    def add_claims_to_access_token(projects):
        return {'prj': projects}

    yield {
        create_access_token(identity=PROJECTS1): PROJECTS1,
        create_access_token(identity=PROJECTS2): PROJECTS2,
    }
