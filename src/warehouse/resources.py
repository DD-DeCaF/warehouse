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
from flask_jwt_extended import jwt_required, jwt_optional, create_access_token, get_jwt_claims

from warehouse.app import app, api, db, jwt
from warehouse.models import Strain, Organism, Namespace, BiologicalEntityType, BiologicalEntity, Medium, Unit, \
    Experiment, Sample, Measurement
from warehouse.utils import CRUD, filter_by_jwt_claims, constraint_check, get_sample_by_id, get_measurement_by_id


base_schema = {
    'project_id': fields.Integer,
    'id': fields.Integer,
    'name': fields.String,
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

sample_schema = api.model('Sample', {
    'experiment_id': fields.Integer,
    'name': fields.String,
    'protocol': fields.String,
    'temperature': fields.Float,
    'gas': fields.String,
    'strain_id': fields.Integer,
    'medium_id': fields.Integer,
})

measurement_schema = api.model('Measurement', {
    'sample_id': fields.Integer,
    'datetime_start': fields.DateTime,
    'datetime_end': fields.DateTime,
    'numerator_id': fields.Integer,
    'denominator_id': fields.Integer,
    'value': fields.Float,
    'unit_id': fields.Integer,
})


@jwt.claims_verification_loader
def project_claims_verification(claims):
    return api.payload is None or ('project_id' not in api.payload) or ('prj' in claims and api.payload['project_id'] in claims['prj'])


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
        @jwt_optional
        @docstring(name_plural)
        def get(self):
            """List all the {}"""
            return CRUD.get(model)

        @api.response(403, 'Forbidden')
        @api.response(404, 'Not Found')
        @api.response(409, 'Constraint is not satisfied')
        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def post(self):
            """Create a {}"""
            return CRUD.post(model, check_permissions=check_permissions)

    @api.route(route + '/<int:id>')
    @api.response(404, 'Not Found')
    @api.param('id', 'The identifier')
    class Item(Resource):
        @api.marshal_with(schema)
        @jwt_optional
        @docstring(name)
        def get(self, id):
            """Get the {} by id"""
            return CRUD.get_by_id(model, id)

        # TODO: archive instead of delete
        @api.response(403, 'Forbidden')
        @jwt_required
        @docstring(name)
        def delete(self, id):
            """Delete the {} by id"""
            CRUD.delete(model, id)

        @api.response(403, 'Forbidden')
        @api.response(409, 'Constraint is not satisfied')
        @api.marshal_with(schema)
        @api.expect(schema)
        @jwt_required
        @docstring(name)
        def put(self, id):
            """Update the {} by id"""
            return CRUD.put(model, id, check_permissions=check_permissions)

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
    @jwt_optional
    def get(self):
        """List all the compounds"""
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
def set_compounds_from_payload(medium):
    compound_dict = {c['id']: c['mass_concentration'] for c in api.payload['compounds']}
    entities = filter_by_jwt_claims(BiologicalEntity).filter(BiologicalEntity.id.in_(compound_dict.keys()))
    if entities.count() < len(api.payload['compounds']):
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
    @jwt_optional
    def get(self):
        """List all the media and their recipes"""
        result = []
        media = CRUD.get(Medium)
        for m in media:
            serialized = serialized_medium_with_mass_concentrations(m)
            result.append(serialized)
        return result

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def post(self):
        """Create a medium by defining the recipe"""
        medium = Medium(
            project_id=api.payload['project_id'],
            name=api.payload['name'],
            ph=api.payload['ph'],
        )
        try:
            set_compounds_from_payload(medium)
        except NotCompound:
            api.abort(404, "No such compound")
        return serialized_medium_with_mass_concentrations(medium)


@api.route('/media/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Media(Resource):
    @api.marshal_with(medium_schema)
    @jwt_optional
    def get(self, id):
        """Get the medium by id"""
        return serialized_medium_with_mass_concentrations(CRUD.get_by_id(Medium, id))

    @jwt_required
    def delete(self, id):
        """Delete the medium by id - compounds will not be deleted"""
        CRUD.delete(Medium, id)

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def put(self, id):
        """Update the medium by id"""
        medium = CRUD.get_by_id(Medium, id)
        try:
            set_compounds_from_payload(medium)
        except NotCompound:
            api.abort(404, "No such compound")
        return serialized_medium_with_mass_concentrations(medium)


@api.route('/experiments/<int:experiment_id>/samples')
@api.response(404, 'Not found')
@api.param('experiment_id', 'The experiment identifier')
class ExperimentSampleList(Resource):
    @api.marshal_with(sample_schema)
    @jwt_optional
    def get(self, experiment_id):
        """List all the samples for the given experiment"""
        return CRUD.get_by_id(Experiment, experiment_id).samples.all()

    @api.marshal_with(sample_schema)
    @api.expect(sample_schema)
    @jwt_required
    def post(self, experiment_id):
        """Create a sample"""
        experiment = CRUD.get_by_id(Experiment, experiment_id)
        sample = CRUD.post(Sample, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'experiment_id': Experiment
        }, project_id=False)
        sample.experiment = experiment
        return sample


@api.route('/samples/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Samples(Resource):
    @api.marshal_with(sample_schema)
    @jwt_optional
    def get(self, id):
        """Get a sample by id"""
        return get_sample_by_id(id)

    @jwt_required
    def delete(self, id):
        """Delete a sample by id - associated measurements will be deleted as well"""
        sample = get_sample_by_id(id)
        db.session.delete(sample)
        constraint_check(db)

    @api.marshal_with(medium_schema)
    @api.expect(medium_simple_schema)
    @jwt_required
    def put(self, id):
        """Update a sample by id"""
        sample = get_sample_by_id(id)
        CRUD.modify_object(sample, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'experiment_id': Experiment
        })
        db.session.merge(sample)
        constraint_check(db)
        return sample


@api.route('/samples/<int:sample_id>/measurements')
class SampleMeasurementList(Resource):
    @api.marshal_with(measurement_schema)
    @jwt_optional
    def get(self, sample_id):
        """List all the measurements for the given sample"""
        sample = self.get_sample_by_id(sample_id)
        return sample.measurements.all()

    @api.marshal_with(measurement_schema)
    @api.expect(measurement_schema)
    @jwt_required
    def post(self, sample_id):
        """Create a measurement for the sample"""
        sample = get_sample_by_id(sample_id)
        measurement = CRUD.post(Measurement, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'sample_id': Sample,
        }, project_id=False)
        measurement.sample = sample
        return measurement


@api.route('/measurements/<int:id>')
@api.response(404, 'Not found')
@api.param('id', 'The identifier')
class Measurements(Resource):
    @api.marshal_with(measurement_schema)
    @jwt_optional
    def get(self, id):
        """Get a measurement by id"""
        return get_measurement_by_id(id)

    @jwt_required
    def delete(self, id):
        """Delete a measurement by id"""
        measurement = get_measurement_by_id(id)
        db.session.delete(measurement)
        constraint_check(db)

    @api.marshal_with(measurement_schema)
    @api.expect(measurement_schema)
    @jwt_required
    def put(self, id):
        """Update a measurement by id"""
        measurement = get_measurement_by_id(id)
        CRUD.modify_object(measurement, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'sample_id': Sample,
        })
        db.session.merge(measurement)
        constraint_check(db)
        return measurement
