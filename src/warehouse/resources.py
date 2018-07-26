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
from flask_restplus import Resource, fields, marshal_with_field

from warehouse.app import api, db
from warehouse.jwt import jwt_required, jwt_require_claim
from warehouse.models import (
    BiologicalEntity, BiologicalEntityType, Experiment, Sample, Medium, Namespace, Organism, Condition, Strain, Unit)
from warehouse.utils import CRUD, constraint_check, filter_by_jwt_claims, get_sample_by_id, get_condition_by_id


base_schema = {
    'project_id': fields.Integer,
    'id': fields.Integer,
    'name': fields.String,
    'created': fields.DateTime,
    'updated': fields.DateTime,
}

organism_schema = api.model('Organism', base_schema)
namespace_schema = api.model('Namespace', base_schema)
type_schema = api.model('BiologicalEntityType', base_schema)
unit_schema = api.model('UnitType', base_schema)

experiment_schema = api.model('Experiment', {**base_schema, **{
    'description': fields.String,
}})

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

medium_compound_schema = api.model('MediumCompound', {**biological_entity_schema, **{
    'mass_concentration': fields.Float
}})

medium_compound_simple_schema = api.model('MediumCompoundSimple', {
    'id': fields.Integer,
    'mass_concentration': fields.Float,
})

medium_schema = api.model('Medium', {**base_schema, **{
    'ph': fields.Float,
    'compounds': fields.List(fields.Nested(medium_compound_schema)),
}})

medium_simple_schema = api.model('MediumSimple', {**base_schema, **{
    'ph': fields.Float,
    'compounds': fields.List(fields.Nested(medium_compound_simple_schema)),
}})

condition_schema = api.model('Condition', {
    'created': fields.DateTime,
    'updated': fields.DateTime,
    'id': fields.Integer,
    'experiment_id': fields.Integer,
    'name': fields.String,
    'protocol': fields.String,
    'temperature': fields.Float,
    'aerobic': fields.Boolean,
    'key_value_store': fields.Raw(
        title='User-defined Key-Value Store',
        description='Field to allow users to add untyped metadata specific to '
                    'each condition',
        required=False, readonly=False,
        example="{'Stirrer Speed' : '300RPM', 'PH' : '7.9'}"
    ),
    'strain_id': fields.Integer,
    'medium_id': fields.Integer,
    'feed_medium_id': fields.Integer,
})

sample_schema = api.model('Sample', {
    'created': fields.DateTime,
    'updated': fields.DateTime,
    'id': fields.Integer,
    'condition_id': fields.Integer,
    'datetime_start': fields.DateTime,
    'datetime_end': fields.DateTime,
    'numerator_id': fields.Integer,
    'denominator_id': fields.Integer,
    'value': fields.Float,
    'unit_id': fields.Integer,
})


def post(obj, *args, **kwargs):
    if isinstance(api.payload, dict):
        return obj.post_one(api.payload, *args, **kwargs)
    elif isinstance(api.payload, list):
        return [obj.post_one(data, *args, **kwargs) for data in api.payload]
    else:
        raise ValueError(f"Unsupported API payload type '{type(api.payload)}'")


def crud_class_factory(model, route, schema, name, name_plural=None, check_permissions=None):
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
        @docstring(name_plural)
        def get(self):
            """List all the {}"""
            # Note: claims are not checked, the query will be filtered by read access
            return CRUD.get(model)

        def post_one(self, data):
            """Create a {}"""
            # TODO: logically, jwt claim check should occur after check for project_id
            if 'project_id' in data:
                jwt_require_claim(data['project_id'], 'write')
            return CRUD.post(data, model, check_permissions=check_permissions)

        @api.response(403, 'Forbidden')
        @api.response(404, 'Not Found')
        @api.response(409, 'Constraint is not satisfied')
        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def post(self):
            """Create a {} (accepts an object or an array of objects)"""
            # Note: claims will be checked later per instance posted
            return post(self)

    @api.route(route + '/<int:id>')
    @api.response(404, 'Not Found')
    @api.param('id', 'The identifier')
    class Item(Resource):
        @api.marshal_with(schema)
        @docstring(name)
        def get(self, id):
            """Get the {} by id"""
            # Note: claims are not checked, the query will be filtered by read access
            return CRUD.get_by_id(model, id)

        # TODO: archive instead of delete
        @api.response(403, 'Forbidden')
        @jwt_required
        @docstring(name)
        def delete(self, id):
            """Delete the {} by id"""
            object_ = CRUD.get_by_id(model, id)
            jwt_require_claim(object_.project_id, 'admin')
            CRUD.delete(model, id)

        @api.response(403, 'Forbidden')
        @api.response(409, 'Constraint is not satisfied')
        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def put(self, id):
            """Update the {} by id"""
            object_ = CRUD.get_by_id(model, id)
            jwt_require_claim(object_.project_id, 'write')
            return CRUD.put(api.payload, model, id, check_permissions=check_permissions)

    return List, Item


OrganismList, Organisms = crud_class_factory(Organism, '/organisms', organism_schema, 'organism')
NamespaceList, Namespaces = crud_class_factory(Namespace, '/namespaces', namespace_schema, 'namespace')
TypeList, Types = crud_class_factory(BiologicalEntityType, '/types', type_schema, 'biological entity type')
UnitList, Units = crud_class_factory(Unit, '/units', unit_schema, 'unit')
ExperimentList, Experiments = crud_class_factory(Experiment, '/experiments', experiment_schema, 'experiment')
StrainList, Strains = crud_class_factory(
    Strain,
    '/strains',
    strain_schema,
    'strain',
    check_permissions={'parent_id': Strain, 'organism_id': Organism},
)
BiologicalEntityList, BiologicalEntities = crud_class_factory(
    BiologicalEntity,
    '/bioentities',
    biological_entity_schema,
    'biological entity',
    'biological entities',
    check_permissions={'namespace_id': Namespace, 'type_id': BiologicalEntityType},
)


# TODO: find out if the speed is an issue
def query_compounds(query):
    return query.join(BiologicalEntity.type).filter(BiologicalEntityType.name == 'compound')


@api.route('/bioentities/compounds')
class Chemicals(Resource):
    @api.marshal_with(biological_entity_schema)
    def get(self):
        """List all the compounds"""
        # Note: claims are not checked, the query will be filtered by read access
        return query_compounds(CRUD.get_query(BiologicalEntity)).all()


@api.marshal_with(medium_schema)
def serialized_medium(medium):
    return medium


@marshal_with_field(fields.List(fields.Nested(medium_compound_schema)))
def serialized_compounds(medium):
    return medium.compounds


def serialized_compounds_with_mass_concentrations(medium):
    # TODO: join?
    compositions = {c.compound_id: c.mass_concentration for c in medium.composition}
    compounds = serialized_compounds(medium)
    for compound in compounds:
        compound['mass_concentration'] = compositions[compound['id']]
    return compounds


def serialized_medium_with_mass_concentrations(m):
    serialized = serialized_medium(m)
    serialized['compounds'] = serialized_compounds_with_mass_concentrations(m)
    return serialized


class NotCompound(Exception):
    pass


# TODO: make a copy if the compounds are from the different project
def set_compounds_from_payload(data, medium):
    compound_dict = {c['id']: c['mass_concentration'] for c in data['compounds']}
    entities = query_compounds(filter_by_jwt_claims(BiologicalEntity)).filter(
        BiologicalEntity.id.in_(compound_dict.keys()))
    if entities.count() < len(data['compounds']):
        raise NotCompound
    medium.compounds = entities.all()
    db.session.add(medium)
    db.session.flush()
    for c in medium.composition:
        c.mass_concentration = compound_dict[c.compound_id]
    constraint_check(db)


@api.route('/media')
class MediaList(Resource):
    @api.marshal_with(medium_schema)
    def get(self):
        """List all the media and their recipes"""
        # Note: claims are not checked, the query will be filtered by read access
        result = []
        media = CRUD.get(Medium)
        for m in media:
            serialized = serialized_medium_with_mass_concentrations(m)
            result.append(serialized)
        return result

    def post_one(self, data):
        """Create one medium"""
        # TODO: logically, jwt claim check should occur after check for project_id
        if 'project_id' in data:
            jwt_require_claim(data['project_id'], 'write')
        medium = Medium(
            project_id=data['project_id'],
            name=data['name'],
            ph=data['ph'],
        )
        try:
            set_compounds_from_payload(data, medium)
        except NotCompound:
            api.abort(404, "No such compound")
        return serialized_medium_with_mass_concentrations(medium)

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def post(self):
        """Create a medium by defining the recipe (accepts an object or an array of objects)"""
        # Note: claims will be checked later per instance posted
        return post(self)


@api.route('/media/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Media(Resource):
    @api.marshal_with(medium_schema)
    def get(self, id):
        """Get the medium by id"""
        return serialized_medium_with_mass_concentrations(CRUD.get_by_id(Medium, id))

    @jwt_required
    def delete(self, id):
        """Delete the medium by id - compounds will not be deleted"""
        medium = CRUD.get_by_id(Medium, id)
        jwt_require_claim(medium.project_id, 'admin')
        CRUD.delete(Medium, id)

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def put(self, id):
        """Update the medium by id"""
        medium = CRUD.get_by_id(Medium, id)
        jwt_require_claim(medium.project_id, 'write')
        try:
            set_compounds_from_payload(api.payload, medium)
        except NotCompound:
            api.abort(404, "No such compound")
        return serialized_medium_with_mass_concentrations(medium)


@api.route('/experiments/<int:experiment_id>/conditions')
@api.response(404, 'Not found')
@api.param('experiment_id', 'The experiment identifier')
class ExperimentConditionList(Resource):
    @api.marshal_with(condition_schema)
    def get(self, experiment_id):
        """List all the conditions for the given experiment"""
        return CRUD.get_by_id(Experiment, experiment_id).conditions.all()

    def post_one(self, data, experiment_id):
        """Create one condition"""
        experiment = CRUD.get_by_id(Experiment, experiment_id)
        jwt_require_claim(experiment.project_id, 'write')
        data['experiment_id'] = experiment_id
        condition = CRUD.post(data, Condition, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'feed_medium_id': Medium,
            'experiment_id': Experiment
        }, project_id=False)
        return condition

    @api.marshal_with(condition_schema)
    @api.expect(condition_schema)
    @jwt_required
    def post(self, experiment_id):
        """Create a condition (accepts an object or an array of objects)"""
        # Note: claims will be checked later per instance posted
        return post(self, experiment_id)


@api.route('/conditions/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Conditions(Resource):
    @api.marshal_with(condition_schema)
    def get(self, id):
        """Get a condition by id"""
        return get_condition_by_id(id)

    @jwt_required
    def delete(self, id):
        """
        Delete a condition by id - associated samples will be deleted
        as well

        """
        condition = get_condition_by_id(id)
        jwt_require_claim(condition.experiment.project_id, 'admin')
        db.session.delete(condition)
        constraint_check(db)

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def put(self, id):
        """Update a condition by id"""
        condition = get_condition_by_id(id)
        jwt_require_claim(condition.experiment.project_id, 'write')
        CRUD.modify_object(api.payload, condition, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'feed_medium_id': Medium,
            'experiment_id': Experiment,
        })
        db.session.merge(condition)
        constraint_check(db)
        return condition


@api.route('/conditions/<int:condition_id>/samples')
class ConditionSampleList(Resource):
    @api.marshal_with(sample_schema)
    def get(self, condition_id):
        """List all the samples for the given condition"""
        condition = get_condition_by_id(condition_id)
        return condition.samples.all()

    def post_one(self, data, condition_id):
        """Post one sample"""
        condition = get_condition_by_id(condition_id)
        jwt_require_claim(condition.experiment.project_id, 'write')
        data['condition_id'] = condition_id
        sample = CRUD.post(data, Sample, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'condition_id': Condition,
        }, project_id=False)
        return sample

    @api.marshal_with(sample_schema)
    @api.expect(sample_schema)
    @jwt_required
    def post(self, condition_id):
        """
        Create samples for the condition (accepts an object or an
        array of objects)

        """
        # Note: claims will be checked later per instance posted
        return post(self, condition_id)


@api.route('/samples/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Samples(Resource):
    @api.marshal_with(sample_schema)
    def get(self, id):
        """Get a sample by id"""
        return get_sample_by_id(id)

    @jwt_required
    def delete(self, id):
        """Delete a sample by id"""
        sample = get_sample_by_id(id)
        jwt_require_claim(sample.condition.experiment.project_id, 'admin')
        db.session.delete(sample)
        constraint_check(db)

    @api.marshal_with(sample_schema)
    @api.expect(sample_schema)
    @jwt_required
    def put(self, id):
        """Update a sample by id"""
        sample = get_sample_by_id(id)
        jwt_require_claim(sample.condition.experiment.project_id, 'write')
        CRUD.modify_object(api.payload, sample, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'condition_id': Condition,
        })
        db.session.merge(sample)
        constraint_check(db)
        return sample
