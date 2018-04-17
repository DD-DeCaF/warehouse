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

"""Implement RESTful API endpoints using resources."""

from flask_restplus import Resource, fields
from flask_jwt_extended import jwt_required, jwt_optional, create_access_token, get_jwt_claims

from warehouse.app import app, api, db, jwt
from warehouse.models import Strain


strain = api.model('Strain', {
    'project_id': fields.Integer,
    'id': fields.Integer,
    'name': fields.String,
    'parent_id': fields.Integer,
    'genotype': fields.String,
})


@jwt.claims_verification_loader
def project_claims_verification(claims):
    app.logger.debug({'claims': claims})
    return api.payload is None or ('prj' in claims and api.payload['project_id'] in claims['prj'])


def filter_by_jwt_claims(query):
    projects = get_jwt_claims().get('prj', [])
    return query.filter(Strain.project_id.in_(projects) | Strain.project_id.is_(None))


def get_object(model, object_id):
    obj = filter_by_jwt_claims(model.query).filter_by(id=object_id).first()
    if obj is None:
        api.abort(404, "{} {} doesn't exist".format(model, object_id))
    return obj


@api.route('/strains')
class Strains(Resource):
    @api.marshal_with(strain)
    @jwt_optional
    def get(self):
        """Get all the strains"""
        return filter_by_jwt_claims(Strain.query).all()

    @api.marshal_with(strain)
    @api.expect(strain)
    @jwt_required
    def post(self):
        """Create strain"""
        app.logger.debug(api.payload)
        strain = Strain(**api.payload)
        app.logger.debug(strain)
        db.session.add(strain)
        db.session.commit()
        return strain


@api.route('/strains/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Strains(Resource):
    @api.marshal_with(strain)
    @jwt_optional
    def get(self, id):
        """Get strain by id"""
        return get_object(Strain, id)

    @api.marshal_with(strain)
    @jwt_required
    def delete(self, id):
        """Delete strain by id"""
        strain = get_object(Strain, id)
        db.session.delete(strain)
        db.session.commit()

    @api.marshal_with(strain)
    @api.expect(strain)
    @jwt_required
    def put(self, id):
        """Update strain by id"""
        strain = get_object(Strain, id)
        for field in api.payload:
            if field != 'id':
                strain[field] = api.payload[field]
        db.session.merge(strain)
        db.session.commit()
