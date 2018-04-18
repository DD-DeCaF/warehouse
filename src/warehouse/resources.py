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
from warehouse.models import Strain, Organism, Namespace, BiologicalEntityType, BiologicalEntity
from warehouse.utils import CRUD


base_schema = {
    'project_id': fields.Integer,
    'id': fields.Integer,
    'name': fields.String,
}

organism_schema = api.model('Organism', base_schema)
namespace_schema = api.model('Namespace', base_schema)
type_schema = api.model('BiologicalEntityType', base_schema)

strain_schema = api.model('Strain', {**base_schema, **{
    'parent_id': fields.Integer,
    'genotype': fields.String,
    'organism_id': fields.Integer,
}})
biological_entity_schema = api.model('BiologicalEntity', {**base_schema, **{
    'namespace_id': fields.Integer,
    'reference': fields.String,
    'type_id': fields.Integer,
}})


@jwt.claims_verification_loader
def project_claims_verification(claims):
    app.logger.debug({'claims': claims})
    return api.payload is None or ('prj' in claims and api.payload['project_id'] in claims['prj'])


def crud_class_factory(model, route, schema, name, name_plural=None):
    if name_plural is None:
        name_plural = name + 's'

    def docstring(*sub):
        def inner(obj):
            obj.__doc__ = obj.__doc__.format(*sub)
            return obj
        return inner

    @api.route(route)
    class List(Resource):
        @api.marshal_with(schema)
        @jwt_optional
        @docstring(name_plural)
        def get(self):
            """Get all the {}"""
            return CRUD.get(model)

        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def post(self):
            """Create a {}"""
            return CRUD.post(model)

    @api.route(route + '/<int:id>')
    @api.response(404, 'Not found')
    @api.param('id', 'The identifier')
    class Item(Resource):
        @api.marshal_with(schema)
        @jwt_optional
        @docstring(name)
        def get(self, id):
            """Get the {} by id"""
            return CRUD.get_by_id(model, id)

        @api.marshal_with(schema)
        @jwt_required
        @docstring(name)
        def delete(self, id):
            """Delete the {} by id"""
            return CRUD.delete(model, id)

        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def put(self, id):
            """Update the {} by id"""
            return CRUD.put(model, id)

    return List, Item


OrganismList, Organisms = crud_class_factory(Organism, '/organisms', organism_schema, 'organism')
StrainList, Strains = crud_class_factory(Strain, '/strains', strain_schema, 'strain')
NamespaceList, Namespaces = crud_class_factory(Namespace, '/namespaces', namespace_schema, 'namespace')
TypeList, Types = crud_class_factory(BiologicalEntityType, '/types', type_schema, 'biological entity type')
BiologicalEntityList, BiologicalEntities = crud_class_factory(
    BiologicalEntity,
    '/bioentities',
    biological_entity_schema,
    'biological entity',
    'biological entities',
)
