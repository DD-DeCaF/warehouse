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

"""Handling and verification of JWT claims"""

from functools import wraps
import logging

from flask import abort, g, jsonify, request
from jose import jwt


logger = logging.getLogger(__name__)


def init_app(app):
    """Add the jwt decoding middleware to the app."""

    @app.before_request
    def decode_jwt():
        if 'Authorization' not in request.headers:
            logger.debug("No JWT provided")
            g.jwt_valid = False
            g.jwt_claims = {'prj': {}}
            return

        try:
            auth = request.headers['Authorization']
            if not auth.startswith('Bearer '):
                raise ValueError("Expected Bearer token authentication")

            _, token = auth.split(' ', 1)
            g.jwt_claims = jwt.decode(token, app.config['JWT_PUBLIC_KEY'], 'RS512')
            g.jwt_valid = True
            logger.debug(f"JWT claims accepted: {g.jwt_claims}")
        except (ValueError, jwt.JWTError, jwt.ExpiredSignatureError, jwt.JWTClaimsError) as e:
            abort(401, f"JWT authentication failed: {e}")


def jwt_required(function):
    """Require JWT authentication to be provided at this endpoint."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        if not g.jwt_valid:
            abort(401, "JWT authentication required")
        return function(*args, **kwargs)
    return wrapper


def project_claims_verification(function):
    from warehouse.resources import api
    @wraps(function)
    def wrapper(*args, **kwargs):
        if api.payload is not None and 'project_id' in api.payload:
            if api.payload['project_id'] not in g.jwt_claims['prj']:
                return {'error': f"No write access to project '{api.payload['project_id']}'"}, 403
        return function(*args, **kwargs)
    return wrapper
