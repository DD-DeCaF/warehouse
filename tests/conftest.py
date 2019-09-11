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

from warehouse import models
from warehouse.app import app as app_
from warehouse.app import init_app
from warehouse.models import db as db_


@pytest.fixture(scope="session")
def app():
    """Provide an initialized Flask for use in certain test cases."""
    init_app(app_)
    with app_.app_context():
        yield app_


@pytest.fixture(scope="session")
def client(app):
    """Provide a Flask test client to be used by almost all test cases."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="session")
def reset_tables(app):
    """Ensure a clean database."""
    # Clean up anything that might reside in the testing database.
    db_.session.remove()
    db_.drop_all()
    # Re-create tables.
    db_.create_all()


@pytest.fixture(scope="session")
def connection():
    """
    Use a connection such that transactions can be used.

    Notes
    -----
    Follows a transaction pattern described in the following:
    http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#session-begin-nested

    """
    with db_.engine.connect() as connection:
        yield connection


@pytest.fixture(scope="function")
def session(reset_tables, connection):
    """
    Create a transaction and session per test unit.

    Rolling back a transaction removes even committed rows
    (``session.commit``) from the database.

    https://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    flask_sqlalchemy_session = db_.session
    transaction = connection.begin()
    db_.session = db_.create_scoped_session(options={"bind": connection, "binds": {}})
    yield db_.session
    db_.session.close()
    transaction.rollback()
    db_.session = flask_sqlalchemy_session


@pytest.fixture(scope="session")
def tokens(app):
    """Provide read, write and admin JWT claims to project 1."""
    return {
        "read": jwt.encode(
            {"prj": {1: "read"}}, app.config["JWT_PRIVATE_KEY"], "RS512"
        ),
        "write": jwt.encode(
            {"prj": {1: "write"}}, app.config["JWT_PRIVATE_KEY"], "RS512"
        ),
        "admin": jwt.encode(
            {"prj": {1: "admin"}}, app.config["JWT_PRIVATE_KEY"], "RS512"
        ),
    }


@pytest.fixture(scope="function")
def data_fixtures(session):
    organism = models.Organism(project_id=1, name="E. coli fixture")
    strain = models.Strain(
        project_id=1,
        name="Strain fixture",
        organism=organism,
        parent=None,
        genotype="Lorem ipsum",
    )
    experiment = models.Experiment(
        project_id=1, name="Experiment fixture", description="Lorem ipsum"
    )
    session.add(organism)
    session.add(strain)
    session.add(experiment)
    session.commit()
    return {"organism": organism, "strain": strain, "experiment": experiment}
