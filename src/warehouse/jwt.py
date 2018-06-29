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


def jwt_require_claim(project_id, required_level):
    """
    Verify that the current user has access to the given project id, and that their access level is equal to or higher
    than the given required level.

    Aborts the request if the user does not have sufficient access.

    :param project_id: The project ID to verify access for
    :param required_level: The required access level (admin, write or read)
    :return: None
    """
    if required_level not in ('admin', 'write', 'read'):
        raise ValueError(f"Invalid claim level '{required_level}'")

    logger.debug(f"Looking for '{required_level}' access to project '{project_id}' in claims '{g.jwt_claims}'")

    # Nobody can write to public projects
    if project_id is None and required_level != 'read':
        abort(403, "Public data can not be modified")

    try:
        authorized = False
        claim_level = g.jwt_claims['prj'][str(project_id)]
    except KeyError:
        # The given project id is not included in the users claims
        abort(403, "You do not have access to the requested resource")

    # The given project id is included in the claims; verify that the access level is sufficient
    if required_level == 'read':
        authorized = True
    elif required_level == 'write' and claim_level in ('admin', 'write'):
        authorized = True
    elif required_level == 'admin' and claim_level == 'admin':
        authorized = True

    if not authorized:
        abort(403, f"This operation requires access level '{required_level}', your access level is '{claim_level}'")
