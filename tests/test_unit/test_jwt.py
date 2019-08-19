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

import pytest
from flask import g
from werkzeug.exceptions import Forbidden, Unauthorized

from warehouse import jwt


def test_jwt_required_decorator(app):
    wrapper = jwt.jwt_required(lambda: None)

    # Valid JWT raises no exception
    g.jwt_valid = True
    wrapper()

    # Invalid JWT raises exception
    g.jwt_valid = False
    with pytest.raises(Unauthorized):
        wrapper()


def test_jwt_require_claim(app):
    # Invalid access level
    with pytest.raises(ValueError):
        jwt.jwt_require_claim(1, "bogus")

    # No write to public projects
    g.jwt_claims = {"prj": {}}
    with pytest.raises(Forbidden):
        jwt.jwt_require_claim(None, "admin")

    # Insufficient access levels
    g.jwt_claims = {"prj": {"1": "read"}}
    with pytest.raises(Forbidden):
        jwt.jwt_require_claim(1, "write")
    with pytest.raises(Forbidden):
        jwt.jwt_require_claim(1, "admin")
    g.jwt_claims = {"prj": {"1": "write"}}
    with pytest.raises(Forbidden):
        jwt.jwt_require_claim(1, "admin")

    # Sufficient access levels
    g.jwt_claims = {"prj": {"1": "read"}}
    jwt.jwt_require_claim(1, "read")
    g.jwt_claims = {"prj": {"1": "write"}}
    jwt.jwt_require_claim(1, "read")
    jwt.jwt_require_claim(1, "write")
    g.jwt_claims = {"prj": {"1": "admin"}}
    jwt.jwt_require_claim(1, "read")
    jwt.jwt_require_claim(1, "write")
    jwt.jwt_require_claim(1, "admin")

    # Missing access level
    g.jwt_claims = {"prj": {"1": "admin"}}
    with pytest.raises(Forbidden):
        jwt.jwt_require_claim(2, "admin")
