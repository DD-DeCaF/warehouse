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
from jose import jwt

from warehouse.app import api
from warehouse.app import app as app_
from warehouse.app import init_app
from warehouse.commands import populate
from warehouse.models import db as db_


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
def db(app):
    """Provide a database session with tables created, populated with the default fixtures."""
    db_.create_all()
    populate()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture(scope="session")
def tokens_admin(app):
    """Provides JWTs with admin claims to different projects"""
    return [{
        'token': jwt.encode({'prj': claims}, app.config['JWT_PRIVATE_KEY'], 'RS512'),
        'claims': claims,
        'projects': list(claims.keys()),
    } for claims in [
        {1: 'admin', 2: 'admin'},
        {4: 'admin'},
    ]]


@pytest.fixture(scope="session")
def tokens_write(app):
    """Provides JWTs with write claims to different projects"""
    return [{
        'token': jwt.encode({'prj': claims}, app.config['JWT_PRIVATE_KEY'], 'RS512'),
        'claims': claims,
        'projects': list(claims.keys()),
    } for claims in [
        {1: 'write', 2: 'write'},
        {4: 'write'},
    ]]


@pytest.fixture(scope="session")
def tokens_read(app):
    """Provides JWTs with read claims to different projects"""
    return [{
        'token': jwt.encode({'prj': claims}, app.config['JWT_PRIVATE_KEY'], 'RS512'),
        'claims': claims,
        'projects': list(claims.keys()),
    } for claims in [
        {1: 'read', 2: 'read'},
        {4: 'read'},
    ]]
