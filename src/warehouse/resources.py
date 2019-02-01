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

from flask import abort
from flask_apispec import FlaskApiSpec, MethodResource, doc, marshal_with, use_kwargs

from warehouse import schemas
from warehouse.app import db
from warehouse.jwt import jwt_require_claim, jwt_required
from warehouse.models import (
    BiologicalEntity, BiologicalEntityType, Condition, Experiment, Medium, Namespace, Organism, Sample, Strain, Unit)
from warehouse.utils import CRUD, constraint_check, filter_by_jwt_claims, get_condition_by_id, get_sample_by_id


def init_app(app):
    """Register API resources on the provided Flask application."""
    def register(path, resource, name):
        app.add_url_rule(path, view_func=resource.as_view(name))
        docs.register(resource, endpoint=name)

    docs = FlaskApiSpec(app)
    register('/organisms', OrganismList, "OrganismList")
    register('/organisms/<int:id>', Organisms, "Organisms")
    register('/namespaces', NamespaceList, "NamespaceList")
    register('/namespaces/<int:id>', Namespaces, "Namespaces")
    register('/types', TypeList, "TypeList")
    register('/types/<int:id>', Types, "Types")
    register('/units', UnitList, "UnitList")
    register('/units/<int:id>', Units, "Units")
    register('/experiments', ExperimentList, "ExperimentList")
    register('/experiments/<int:id>', Experiments, "Experiments")
    register('/strains', StrainList, "StrainList")
    register('/strains/<int:id>', Strains, "Strains")
    register('/bioentities', BiologicalEntityList, "BiologicalEntityList")
    register('/bioentities/<int:id>', BiologicalEntities, "BiologicalEntities")
    register('/bioentities/compounds', Chemicals, "Chemicals")
    register('/media', MediaList, "MediaList")
    register('/media/<int:id>', Media, "Media")
    register('/experiments/<int:experiment_id>/conditions', ExperimentConditionList, "ExperimentConditionList")
    register('/conditions/<int:id>', Conditions, "Conditions")
    register('/conditions/<int:condition_id>/data', ConditionDataList, "ConditionDataList")
    register('/conditions/<int:condition_id>/samples', ConditionSampleList, "ConditionSampleList")
    register('/samples/<int:id>', Samples, "Samples")


def crud_class_factory(model, schema, name, name_plural=None, check_permissions=None):
    if name_plural is None:
        name_plural = name + 's'

    class List(MethodResource):
        @marshal_with(schema(many=True))
        @doc(f"List all the {name_plural}")
        def get(self):
            # Note: claims are not checked, the query will be filtered by read access
            return CRUD.get(model)

        @jwt_required
        @use_kwargs(schema)
        @marshal_with(schema, 200)
        @marshal_with(None, 403)
        @marshal_with(None, 404)
        @marshal_with(None, 409)
        @doc(f"Create a {name}")
        def post(self, **payload):
            # TODO: logically, jwt claim check should occur after check for project_id
            if 'project_id' in payload:
                jwt_require_claim(payload['project_id'], 'write')
            return CRUD.post(payload, model, check_permissions=check_permissions)


    class Item(MethodResource):
        @marshal_with(schema)
        @doc(f"Get the {name} by id")
        def get(self, id):
            # Note: claims are not checked, the query will be filtered by read access
            return CRUD.get_by_id(model, id)

        # TODO: archive instead of delete
        @jwt_required
        @marshal_with(None, 403)
        @marshal_with(None, 404)
        @doc(f"Delete the {name} by id")
        def delete(self, id):
            object_ = CRUD.get_by_id(model, id)
            jwt_require_claim(object_.project_id, 'admin')
            CRUD.delete(model, id)

        @jwt_required
        @use_kwargs(schema)
        @marshal_with(schema, 200)
        @marshal_with(None, 403)
        @marshal_with(None, 404)
        @marshal_with(None, 409)
        @doc(f"Update the {name} by id")
        def put(self, id, **payload):
            object_ = CRUD.get_by_id(model, id)
            jwt_require_claim(object_.project_id, 'write')
            return CRUD.put(payload, model, id, check_permissions=check_permissions)

    return List, Item


OrganismList, Organisms = crud_class_factory(Organism, schemas.Organism, 'organism')
NamespaceList, Namespaces = crud_class_factory(Namespace, schemas.Namespace, 'namespace')
TypeList, Types = crud_class_factory(BiologicalEntityType, schemas.BiologicalEntityType, 'biological entity type')
UnitList, Units = crud_class_factory(Unit, schemas.Unit, 'unit')
ExperimentList, Experiments = crud_class_factory(Experiment, schemas.Experiment, 'experiment')
StrainList, Strains = crud_class_factory(
    Strain,
    schemas.Strain,
    'strain',
    check_permissions={'parent_id': Strain, 'organism_id': Organism},
)
BiologicalEntityList, BiologicalEntities = crud_class_factory(
    BiologicalEntity,
    schemas.BiologicalEntity,
    'biological entity',
    'biological entities',
    check_permissions={'namespace_id': Namespace, 'type_id': BiologicalEntityType},
)


# TODO: find out if the speed is an issue
def query_compounds(query):
    return query.join(BiologicalEntity.type).filter(BiologicalEntityType.name == 'compound')


class Chemicals(MethodResource):
    @marshal_with(schemas.BiologicalEntity(many=True))
    @doc(description="List all the compounds")
    def get(self):
        # Note: claims are not checked, the query will be filtered by read access
        return query_compounds(CRUD.get_query(BiologicalEntity)).all()


class NotCompound(Exception):
    pass


def medium_with_mass_concentrations(medium):
    compositions = {c.compound_id: c.mass_concentration for c in medium.composition}
    for compound in medium.compounds:
        compound.mass_concentration = compositions[compound.id]
    return medium


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


class MediaList(MethodResource):
    @marshal_with(schemas.Medium(many=True))
    @doc(description="List all the media and their recipes")
    def get(self):
        # Note: claims are not checked, the query will be filtered by read access
        result = []
        media = CRUD.get(Medium)
        for m in media:
            serialized = medium_with_mass_concentrations(m)
            result.append(serialized)
        return result

    @jwt_required
    @use_kwargs(schemas.MediumSimple)
    @marshal_with(schemas.Medium)
    @doc(description="Create one medium by defining the recipe")
    def post(self, **payload):
        # TODO: logically, jwt claim check should occur after check for project_id
        if 'project_id' in payload:
            jwt_require_claim(payload['project_id'], 'write')
        medium = Medium(
            project_id=payload['project_id'],
            name=payload['name'],
            ph=payload['ph'],
        )
        try:
            set_compounds_from_payload(payload, medium)
        except NotCompound:
            abort(404, "No such compound")
        return medium_with_mass_concentrations(medium)


class Media(MethodResource):
    @marshal_with(schemas.Medium)
    @doc(description="Get the medium by id")
    def get(self, id):
        return medium_with_mass_concentrations(CRUD.get_by_id(Medium, id))

    @jwt_required
    @doc(description="Delete the medium by id - compounds will not be deleted")
    def delete(self, id):
        medium = CRUD.get_by_id(Medium, id)
        jwt_require_claim(medium.project_id, 'admin')
        CRUD.delete(Medium, id)

    @jwt_required
    @use_kwargs(schemas.MediumSimple)
    @marshal_with(schemas.Medium, 200)
    @marshal_with(None, 404)
    @doc(description="Update the medium by id")
    def put(self, id, **payload):
        medium = CRUD.get_by_id(Medium, id)
        jwt_require_claim(medium.project_id, 'write')
        try:
            set_compounds_from_payload(payload, medium)
        except NotCompound:
            abort(404, "No such compound")
        return medium_with_mass_concentrations(medium)


class ExperimentConditionList(MethodResource):
    @marshal_with(schemas.Condition(many=True))
    @doc(description="List all the conditions for the given experiment")
    def get(self, experiment_id):
        return CRUD.get_by_id(Experiment, experiment_id).conditions.all()

    @jwt_required
    @use_kwargs(schemas.Condition)
    @marshal_with(schemas.Condition)
    @doc(description="Create one condition")
    def post(self, experiment_id, **payload):
        experiment = CRUD.get_by_id(Experiment, experiment_id)
        jwt_require_claim(experiment.project_id, 'write')
        payload['experiment_id'] = experiment_id
        condition = CRUD.post(payload, Condition, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'feed_medium_id': Medium,
            'experiment_id': Experiment
        }, project_id=False)
        return condition


class Conditions(MethodResource):
    @marshal_with(schemas.Condition, 200)
    @marshal_with(None, 404)
    @doc(description="Get a condition by id")
    def get(self, id):
        return get_condition_by_id(id)

    @jwt_required
    @marshal_with(None, 404)
    @doc(description="Delete a condition by id - associated samples will be deleted as well")
    def delete(self, id):
        condition = get_condition_by_id(id)
        jwt_require_claim(condition.experiment.project_id, 'admin')
        db.session.delete(condition)
        constraint_check(db)

    @jwt_required
    @use_kwargs(schemas.Condition)
    @marshal_with(schemas.Condition, 200)
    @marshal_with(None, 404)
    @doc(description="Update a condition by id")
    def put(self, id, **payload):
        condition = get_condition_by_id(id)
        jwt_require_claim(condition.experiment.project_id, 'write')
        CRUD.modify_object(payload, condition, check_permissions={
            'strain_id': Strain,
            'medium_id': Medium,
            'feed_medium_id': Medium,
            'experiment_id': Experiment,
        })
        db.session.merge(condition)
        constraint_check(db)
        return condition


class ConditionDataList(MethodResource):
    @marshal_with(schemas.ModelingData())
    @doc(description="List modeling data for the given condition")
    def get(self, condition_id):
        condition = get_condition_by_id(condition_id)

        def bigg_namespace(namespace, type):
            """Correct the BIGG namespace to the actual miriam identifier."""
            if namespace == "BIGG":
                if type == "metabolite":
                    return "bigg.metabolite"
                elif type == "reaction":
                    return "bigg.reaction"
            return namespace

        medium = [{
            'id': compound.reference,
            'namespace': bigg_namespace(compound.namespace.name, "metabolite"),
        } for compound in condition.medium.compounds]

        def iterate(genotype, strain):
            genotype.append(strain.genotype)
            if strain.parent:
                iterate(genotype, strain.parent[0])
            return genotype
        genotype = iterate([], condition.strain)

        measurements = []
        for sample in condition.samples.all():
            if sample.numerator is None and sample.denominator is None and sample.unit.name == "growth (1/h)":
                measurements.append({
                    'id': None,
                    'namespace': None,
                    'measurements': [sample.value],
                    'type': "growth-rate",
                })
            elif sample.denominator is None and sample.numerator.type.name == 'reaction':
                measurements.append({
                    'id': sample.numerator.reference,
                    'namespace': bigg_namespace(sample.numerator.namespace.name, "reaction"),
                    'measurements': [sample.value],
                    'type': sample.numerator.type.name,
                })
            # TODO (Ali Kaafarani): include compound measurements
            # TODO (Ali Kaafarani): include proteomics

        return {
            'medium': medium,
            'genotype': genotype,
            'measurements': measurements,
        }


class ConditionSampleList(MethodResource):
    @marshal_with(schemas.Sample(many=True))
    @doc(description="List all the samples for the given condition")
    def get(self, condition_id):
        condition = get_condition_by_id(condition_id)
        return condition.samples.all()

    @jwt_required
    @use_kwargs(schemas.Sample)
    @marshal_with(schemas.Sample)
    @doc(description="Create a sample for the condition")
    def post(self, condition_id, **payload):
        condition = get_condition_by_id(condition_id)
        jwt_require_claim(condition.experiment.project_id, 'write')
        payload['condition_id'] = condition_id
        sample = CRUD.post(payload, Sample, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'condition_id': Condition,
        }, project_id=False)
        return sample


class Samples(MethodResource):
    @marshal_with(schemas.Sample, 200)
    @marshal_with(None, 404)
    @doc(description="Get a sample by id")
    def get(self, id):
        return get_sample_by_id(id)

    @jwt_required
    @marshal_with(None, 404)
    @doc(description="Delete a sample by id")
    def delete(self, id):
        sample = get_sample_by_id(id)
        jwt_require_claim(sample.condition.experiment.project_id, 'admin')
        db.session.delete(sample)
        constraint_check(db)

    @jwt_required
    @use_kwargs(schemas.Sample)
    @marshal_with(schemas.Sample, 200)
    @marshal_with(None, 404)
    @doc(description="Update a sample by id")
    def put(self, id, **payload):
        sample = get_sample_by_id(id)
        jwt_require_claim(sample.condition.experiment.project_id, 'write')
        CRUD.modify_object(payload, sample, check_permissions={
            'numerator_id': BiologicalEntity,
            'denominator_id': BiologicalEntity,
            'unit_id': Unit,
            'condition_id': Condition,
        })
        db.session.merge(sample)
        constraint_check(db)
        return sample
