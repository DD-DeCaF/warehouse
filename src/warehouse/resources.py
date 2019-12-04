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

import warnings

from flask import abort, g, make_response
from flask_apispec import FlaskApiSpec, MethodResource, marshal_with, use_kwargs
from sqlalchemy.orm.exc import NoResultFound

from warehouse import models, schemas
from warehouse.app import db
from warehouse.jwt import jwt_require_claim, jwt_required
from warehouse.utils import verify_relation


def init_app(app):
    """Register API resources on the provided Flask application."""

    def register(path, resource):
        app.add_url_rule(path, view_func=resource.as_view(resource.__name__))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            docs.register(resource, endpoint=resource.__name__)

    docs = FlaskApiSpec(app)
    register("/organisms", Organisms)
    register("/organisms/<int:id>", Organism)
    register("/strains", Strains)
    register("/strains/<int:id>", Strain)
    register("/experiments", Experiments)
    register("/experiments/<int:id>", Experiment)
    register("/media", Media)
    register("/media/<int:id>", Medium)
    register("/media/compounds", MediumCompounds)
    register("/media/compounds/<int:id>", MediumCompound)
    register("/conditions", Conditions)
    register("/conditions/<int:id>", Condition)
    register("/conditions/<int:id>/data", ConditionData)
    register("/samples", Samples)
    register("/samples/<int:id>", Sample)
    register("/fluxomics", Fluxomics)
    register("/fluxomics/batch", FluxomicsBatch)
    register("/fluxomics/<int:id>", Fluxomic)
    register("/metabolomics", Metabolomics)
    register("/metabolomics/batch", MetabolomicsBatch)
    register("/metabolomics/<int:id>", Metabolomic)
    register("/proteomics", Proteomics)
    register("/proteomics/batch", ProteomicsBatch)
    register("/proteomics/<int:id>", Proteomic)
    register("/uptake-secretion-rates", UptakeSecretionRates)
    register("/uptake-secretion-rates/<int:id>", UptakeSecretionRate)
    register("/molar-yields", MolarYields)
    register("/molar-yields/<int:id>", MolarYield)
    register("/growth-rates", GrowthRates)
    register("/growth-rates/<int:id>", GrowthRate)


class Organisms(MethodResource):
    @marshal_with(schemas.Organism(many=True), 200)
    def get(self):
        return models.Organism.query.filter(
            models.Organism.project_id.in_(g.jwt_claims["prj"])
            | models.Organism.project_id.is_(None)
        ).all()

    @jwt_required
    @use_kwargs(schemas.Organism(exclude=("id",)))
    @marshal_with(schemas.Organism(only=("id",)), 201)
    def post(self, project_id, name):
        jwt_require_claim(project_id, "write")
        organism = models.Organism(project_id=project_id, name=name)
        db.session.add(organism)
        db.session.commit()
        return (organism, 201)


class Organism(MethodResource):
    @marshal_with(schemas.Organism, 200)
    def get(self, id):
        try:
            return (
                models.Organism.query.filter(models.Organism.id == id)
                .filter(
                    models.Organism.project_id.in_(g.jwt_claims["prj"])
                    | models.Organism.project_id.is_(None)
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Organism(exclude=("id",), partial=True))
    @marshal_with(schemas.Organism(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            organism = (
                models.Organism.query.filter(models.Organism.id == id)
                .filter(models.Organism.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(organism.project_id, "write")
            # If modifying the project id, make sure the user has write permissions to
            # the new project too.
            if "project_id" in payload:
                jwt_require_claim(payload["project_id"], "write")
            for field, value in payload.items():
                setattr(organism, field, value)
            db.session.add(organism)
            db.session.commit()
            return (organism, 200)

    @jwt_required
    def delete(self, id):
        try:
            organism = (
                models.Organism.query.filter(models.Organism.id == id)
                .filter(models.Organism.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(organism.project_id, "admin")
            db.session.delete(organism)
            db.session.commit()
            return make_response("", 204)


class Strains(MethodResource):
    @marshal_with(schemas.Strain(many=True), 200)
    def get(self):
        return models.Strain.query.filter(
            models.Strain.project_id.in_(g.jwt_claims["prj"])
            | models.Strain.project_id.is_(None)
        ).all()

    @jwt_required
    @use_kwargs(schemas.Strain(exclude=("id",)))
    @marshal_with(schemas.Strain(only=("id",)), 201)
    def post(self, project_id, organism_id, parent_id, name, genotype):
        jwt_require_claim(project_id, "write")
        # Verify the relations
        organism = verify_relation(models.Organism, organism_id)
        if parent_id:
            parent = verify_relation(models.Strain, parent_id)
        else:
            parent = None
        strain = models.Strain(
            project_id=project_id,
            organism=organism,
            parent=parent,
            name=name,
            genotype=genotype,
        )
        db.session.add(strain)
        db.session.commit()
        return (strain, 201)


class Strain(MethodResource):
    @marshal_with(schemas.Strain, 200)
    def get(self, id):
        try:
            return (
                models.Strain.query.filter(models.Strain.id == id)
                .filter(
                    models.Strain.project_id.in_(g.jwt_claims["prj"])
                    | models.Strain.project_id.is_(None)
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Strain(exclude=("id",), partial=True))
    @marshal_with(schemas.Strain(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            strain = (
                models.Strain.query.filter(models.Strain.id == id)
                .filter(models.Strain.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(strain.project_id, "write")
            # If modifying the project id, make sure the user has write permissions to
            # the new project too.
            if "project_id" in payload:
                jwt_require_claim(payload["project_id"], "write")
            for field, value in payload.items():
                setattr(strain, field, value)
            db.session.add(strain)
            db.session.commit()
            return (strain, 200)

    @jwt_required
    def delete(self, id):
        try:
            strain = (
                models.Strain.query.filter(models.Strain.id == id)
                .filter(models.Strain.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(strain.project_id, "admin")
            db.session.delete(strain)
            db.session.commit()
            return make_response("", 204)


class Experiments(MethodResource):
    @marshal_with(schemas.Experiment(many=True), 200)
    def get(self):
        return models.Experiment.query.filter(
            models.Experiment.project_id.in_(g.jwt_claims["prj"])
            | models.Experiment.project_id.is_(None)
        ).all()

    @jwt_required
    @use_kwargs(schemas.Experiment(exclude=("id",)))
    @marshal_with(schemas.Experiment(only=("id",)), 201)
    def post(self, project_id, name, description):
        jwt_require_claim(project_id, "write")
        experiment = models.Experiment(
            project_id=project_id, name=name, description=description
        )
        db.session.add(experiment)
        db.session.commit()
        return (experiment, 201)


class Experiment(MethodResource):
    @marshal_with(schemas.Experiment, 200)
    def get(self, id):
        try:
            return (
                models.Experiment.query.filter(models.Experiment.id == id)
                .filter(
                    models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    | models.Experiment.project_id.is_(None)
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Experiment(exclude=("id",), partial=True))
    @marshal_with(schemas.Experiment(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            experiment = (
                models.Experiment.query.filter(models.Experiment.id == id)
                .filter(models.Experiment.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(experiment.project_id, "write")
            # If modifying the project id, make sure the user has write permissions to
            # the new project too.
            if "project_id" in payload:
                jwt_require_claim(payload["project_id"], "write")
            for field, value in payload.items():
                setattr(experiment, field, value)
            db.session.add(experiment)
            db.session.commit()
            return (experiment, 200)

    @jwt_required
    def delete(self, id):
        try:
            experiment = (
                models.Experiment.query.filter(models.Experiment.id == id)
                .filter(models.Experiment.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(experiment.project_id, "admin")
            db.session.delete(experiment)
            db.session.commit()
            return make_response("", 204)


class Media(MethodResource):
    @marshal_with(schemas.Medium(many=True), 200)
    def get(self):
        return models.Medium.query.filter(
            models.Medium.project_id.in_(g.jwt_claims["prj"])
            | models.Medium.project_id.is_(None)
        ).all()

    @jwt_required
    @use_kwargs(schemas.Medium(exclude=("id",)))
    @marshal_with(schemas.Medium(only=("id",)), 201)
    def post(self, project_id, name):
        jwt_require_claim(project_id, "write")
        medium = models.Medium(project_id=project_id, name=name)
        db.session.add(medium)
        db.session.commit()
        return (medium, 201)


class Medium(MethodResource):
    @marshal_with(schemas.Medium, 200)
    def get(self, id):
        try:
            return (
                models.Medium.query.filter(models.Medium.id == id)
                .filter(
                    models.Medium.project_id.in_(g.jwt_claims["prj"])
                    | models.Medium.project_id.is_(None)
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Medium(exclude=("id",), partial=True))
    @marshal_with(schemas.Medium(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            medium = (
                models.Medium.query.filter(models.Medium.id == id)
                .filter(models.Medium.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(medium.project_id, "write")
            # If modifying the project id, make sure the user has write permissions to
            # the new project too.
            if "project_id" in payload:
                jwt_require_claim(payload["project_id"], "write")
            for field, value in payload.items():
                setattr(medium, field, value)
            db.session.add(medium)
            db.session.commit()
            return (medium, 200)

    @jwt_required
    def delete(self, id):
        try:
            medium = (
                models.Medium.query.filter(models.Medium.id == id)
                .filter(models.Medium.project_id.in_(g.jwt_claims["prj"]))
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(medium.project_id, "admin")
            db.session.delete(medium)
            db.session.commit()
            return make_response("", 204)


class MediumCompounds(MethodResource):
    @marshal_with(schemas.MediumCompound(many=True), 200)
    def get(self):
        return models.MediumCompound.query.filter(
            models.MediumCompound.medium.has(
                models.Medium.project_id.in_(g.jwt_claims["prj"])
            )
            | models.MediumCompound.medium.has(models.Medium.project_id.is_(None))
        ).all()

    @jwt_required
    @use_kwargs(schemas.MediumCompound(exclude=("id",)))
    @marshal_with(schemas.MediumCompound(only=("id",)), 201)
    def post(
        self,
        medium_id,
        compound_name,
        compound_identifier,
        compound_namespace,
        mass_concentration,
    ):
        medium = verify_relation(models.Medium, medium_id)
        jwt_require_claim(medium.project_id, "write")
        medium_compound = models.MediumCompound(
            medium_id=medium_id,
            compound_name=compound_name,
            compound_identifier=compound_identifier,
            compound_namespace=compound_namespace,
            mass_concentration=mass_concentration,
        )
        db.session.add(medium_compound)
        db.session.commit()
        return (medium_compound, 201)


class MediumCompound(MethodResource):
    @marshal_with(schemas.MediumCompound, 200)
    def get(self, id):
        try:
            return (
                models.MediumCompound.query.filter(models.MediumCompound.id == id)
                .filter(
                    models.MediumCompound.medium.has(
                        models.Medium.project_id.in_(g.jwt_claims["prj"])
                    )
                    | models.MediumCompound.medium.has(
                        models.Medium.project_id.is_(None)
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.MediumCompound(exclude=("id",), partial=True))
    @marshal_with(schemas.MediumCompound(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            medium_compound = (
                models.MediumCompound.query.filter(models.MediumCompound.id == id)
                .filter(
                    models.MediumCompound.medium.has(
                        models.Medium.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(medium_compound.medium.project_id, "write")
            for field, value in payload.items():
                setattr(medium_compound, field, value)
            db.session.add(medium_compound)
            db.session.commit()
            return (medium_compound, 200)

    @jwt_required
    def delete(self, id):
        try:
            medium_compound = (
                models.MediumCompound.query.filter(models.MediumCompound.id == id)
                .filter(
                    models.MediumCompound.medium.has(
                        models.Medium.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(medium_compound.medium.project_id, "admin")
            db.session.delete(medium_compound)
            db.session.commit()
            return make_response("", 204)


class Conditions(MethodResource):
    @marshal_with(schemas.Condition(many=True), 200)
    def get(self):
        return models.Condition.query.filter(
            models.Condition.experiment.has(
                models.Experiment.project_id.in_(g.jwt_claims["prj"])
            )
            | models.Condition.experiment.has(models.Experiment.project_id.is_(None))
        ).all()

    @jwt_required
    @use_kwargs(schemas.Condition(exclude=("id",)))
    @marshal_with(schemas.Condition(only=("id",)), 201)
    def post(self, experiment_id, strain_id, medium_id, name):
        experiment = verify_relation(models.Experiment, experiment_id)
        strain = verify_relation(models.Strain, strain_id)
        medium = verify_relation(models.Medium, medium_id)
        jwt_require_claim(experiment.project_id, "write")
        condition = models.Condition(
            experiment=experiment, strain=strain, medium=medium, name=name
        )
        db.session.add(condition)
        db.session.commit()
        return (condition, 201)


class Condition(MethodResource):
    @marshal_with(schemas.Condition, 200)
    def get(self, id):
        try:
            return (
                models.Condition.query.filter(models.Condition.id == id)
                .filter(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                    | models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Condition(exclude=("id",), partial=True))
    @marshal_with(schemas.Condition(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            condition = (
                models.Condition.query.filter(models.Condition.id == id)
                .filter(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(condition.experiment.project_id, "write")
            for field, value in payload.items():
                setattr(condition, field, value)
            db.session.add(condition)
            db.session.commit()
            return (condition, 200)

    @jwt_required
    def delete(self, id):
        try:
            condition = (
                models.Condition.query.filter(models.Condition.id == id)
                .filter(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(condition.experiment.project_id, "admin")
            db.session.delete(condition)
            db.session.commit()
            return make_response("", 204)


class Samples(MethodResource):
    @marshal_with(schemas.Sample(many=True), 200)
    def get(self):
        return models.Sample.query.filter(
            models.Sample.condition.has(
                models.Experiment.project_id.in_(g.jwt_claims["prj"])
            )
            | models.Sample.condition.has(models.Experiment.project_id.is_(None))
        ).all()

    @jwt_required
    @use_kwargs(schemas.Sample(exclude=("id",)))
    @marshal_with(schemas.Sample(only=("id",)), 201)
    def post(self, condition_id, start_time, end_time):
        try:
            condition = models.Condition.query.filter(
                models.Condition.id == condition_id
            ).one()
            jwt_require_claim(condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {condition_id} does not exist")
        sample = models.Sample(
            condition=condition, start_time=start_time, end_time=end_time
        )
        db.session.add(sample)
        db.session.commit()
        return (sample, 201)


class ConditionData(MethodResource):
    @marshal_with(schemas.ConditionData())
    def get(self, id):
        try:
            return (
                models.Condition.query.filter(models.Condition.id == id)
                .filter(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                    | models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")


class Sample(MethodResource):
    @marshal_with(schemas.Sample, 200)
    def get(self, id):
        try:
            return (
                models.Sample.query.filter(models.Sample.id == id)
                .filter(
                    models.Sample.condition.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                    | models.Sample.condition.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Sample(exclude=("id",), partial=True))
    @marshal_with(schemas.Sample(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            sample = (
                models.Sample.query.filter(models.Sample.id == id)
                .filter(
                    models.Sample.condition.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(sample.condition.experiment.project_id, "write")
            for field, value in payload.items():
                setattr(sample, field, value)
            db.session.add(sample)
            db.session.commit()
            return (sample, 200)

    @jwt_required
    def delete(self, id):
        try:
            sample = (
                models.Sample.query.filter(models.Sample.id == id)
                .filter(
                    models.Sample.condition.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(sample.condition.experiment.project_id, "admin")
            db.session.delete(sample)
            db.session.commit()
            return make_response("", 204)


class Fluxomics(MethodResource):
    @marshal_with(schemas.Fluxomics(many=True), 200)
    def get(self):
        return models.Fluxomics.query.filter(
            models.Fluxomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.Fluxomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.Fluxomics(exclude=("id",)))
    @marshal_with(schemas.Fluxomics(only=("id",)), 201)
    def post(
        self,
        sample_id,
        reaction_name,
        reaction_identifier,
        reaction_namespace,
        measurement,
        uncertainty,
    ):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        fluxomics = models.Fluxomics(
            sample=sample,
            reaction_name=reaction_name,
            reaction_identifier=reaction_identifier,
            reaction_namespace=reaction_namespace,
            measurement=measurement,
            uncertainty=uncertainty,
        )
        db.session.add(fluxomics)
        db.session.commit()
        return (fluxomics, 201)


class FluxomicsBatch(MethodResource):
    @jwt_required
    @use_kwargs(schemas.FluxomicsBatchRequest)
    @marshal_with(schemas.Fluxomics(only=("id",), many=True), 201)
    def post(self, body):
        fluxomics = []
        verified_project_ids = set()
        for fluxomics_item in body:
            try:
                sample = models.Sample.query.filter(
                    models.Sample.id == fluxomics_item["sample_id"]
                ).one()

                project_id = sample.condition.experiment.project_id
                
                if project_id not in verified_project_ids:
                    jwt_require_claim(project_id, "write")
                    verified_project_ids.add(project_id)

                fluxomics.append(
                    models.Fluxomics(
                        sample=sample,
                        reaction_name=fluxomics_item["reaction_name"],
                        reaction_identifier=fluxomics_item["reaction_identifier"],
                        reaction_namespace=fluxomics_item["reaction_namespace"],
                        measurement=fluxomics_item["measurement"],
                        uncertainty=fluxomics_item["uncertainty"],
                    )
                )
            except NoResultFound:
                abort(
                    404, f"Related object {fluxomics_item['sample_id']} does not exist"
                )
        db.session.add_all(fluxomics)
        db.session.commit()
        return (fluxomics, 201)


class Fluxomic(MethodResource):
    @marshal_with(schemas.Fluxomics, 200)
    def get(self, id):
        try:
            return (
                models.Fluxomics.query.filter(models.Fluxomics.id == id)
                .filter(
                    models.Fluxomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.Fluxomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Fluxomics(exclude=("id",), partial=True))
    @marshal_with(schemas.Fluxomics(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            fluxomics = (
                models.Fluxomics.query.filter(models.Fluxomics.id == id)
                .filter(
                    models.Fluxomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(fluxomics.sample.condition.experiment.project_id, "write")
            for field, value in payload.items():
                setattr(fluxomics, field, value)
            db.session.add(fluxomics)
            db.session.commit()
            return (fluxomics, 200)

    @jwt_required
    def delete(self, id):
        try:
            fluxomics = (
                models.Fluxomics.query.filter(models.Fluxomics.id == id)
                .filter(
                    models.Fluxomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(fluxomics.sample.condition.experiment.project_id, "admin")
            db.session.delete(fluxomics)
            db.session.commit()
            return make_response("", 204)


class Metabolomics(MethodResource):
    @marshal_with(schemas.Metabolomics(many=True), 200)
    def get(self):
        return models.Metabolomics.query.filter(
            models.Metabolomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.Metabolomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.Metabolomics(exclude=("id",)))
    @marshal_with(schemas.Metabolomics(only=("id",)), 201)
    def post(
        self,
        sample_id,
        compound_name,
        compound_identifier,
        compound_namespace,
        measurement,
        uncertainty,
    ):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        metabolomics = models.Metabolomics(
            sample=sample,
            compound_name=compound_name,
            compound_identifier=compound_identifier,
            compound_namespace=compound_namespace,
            measurement=measurement,
            uncertainty=uncertainty,
        )
        db.session.add(metabolomics)
        db.session.commit()
        return (metabolomics, 201)


class MetabolomicsBatch(MethodResource):
    @jwt_required
    @use_kwargs(schemas.MetabolomicsBatchRequest)
    @marshal_with(schemas.Metabolomics(only=("id",), many=True), 201)
    def post(self, body):
        metabolomics = []
        verified_project_ids = set()
        for metabolomics_item in body:
            try:
                sample = models.Sample.query.filter(
                    models.Sample.id == metabolomics_item["sample_id"]
                ).one()

                project_id = sample.condition.experiment.project_id
                
                if project_id not in verified_project_ids:
                    jwt_require_claim(project_id, "write")
                    verified_project_ids.add(project_id)

                metabolomics.append(
                    models.Metabolomics(
                        sample=sample,
                        compound_name=metabolomics_item["compound_name"],
                        compound_identifier=metabolomics_item["compound_identifier"],
                        compound_namespace=metabolomics_item["compound_namespace"],
                        measurement=metabolomics_item["measurement"],
                        uncertainty=metabolomics_item["uncertainty"],
                    )
                )
            except NoResultFound:
                abort(
                    404, f"Related object {metabolomics_item['sample_id']} does not exist"
                )
        db.session.add_all(metabolomics)
        db.session.commit()
        return (metabolomics, 201)


class Metabolomic(MethodResource):
    @marshal_with(schemas.Metabolomics, 200)
    def get(self, id):
        try:
            return (
                models.Metabolomics.query.filter(models.Metabolomics.id == id)
                .filter(
                    models.Metabolomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.Metabolomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Metabolomics(exclude=("id",), partial=True))
    @marshal_with(schemas.Metabolomics(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            metabolomics = (
                models.Metabolomics.query.filter(models.Metabolomics.id == id)
                .filter(
                    models.Metabolomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                metabolomics.sample.condition.experiment.project_id, "write"
            )
            for field, value in payload.items():
                setattr(metabolomics, field, value)
            db.session.add(metabolomics)
            db.session.commit()
            return (metabolomics, 200)

    @jwt_required
    def delete(self, id):
        try:
            metabolomics = (
                models.Metabolomics.query.filter(models.Metabolomics.id == id)
                .filter(
                    models.Metabolomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                metabolomics.sample.condition.experiment.project_id, "admin"
            )
            db.session.delete(metabolomics)
            db.session.commit()
            return make_response("", 204)


class Proteomics(MethodResource):
    @marshal_with(schemas.Proteomics(many=True), 200)
    def get(self):
        return models.Proteomics.query.filter(
            models.Proteomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.Proteomics.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.Proteomics(exclude=("id",)))
    @marshal_with(schemas.Proteomics(only=("id",)), 201)
    def post(
        self, sample_id, identifier, name, full_name, gene, measurement, uncertainty
    ):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        proteomics = models.Proteomics(
            sample=sample,
            identifier=identifier,
            name=name,
            full_name=full_name,
            gene=gene,
            measurement=measurement,
            uncertainty=uncertainty,
        )
        db.session.add(proteomics)
        db.session.commit()
        return (proteomics, 201)


class ProteomicsBatch(MethodResource):
    @jwt_required
    @use_kwargs(schemas.ProteomicsBatchRequest)
    @marshal_with(schemas.Proteomics(only=("id",), many=True), 201)
    def post(self, body):
        proteomics = []
        verified_project_ids = set()
        for proteomics_item in body:
            try:
                sample = models.Sample.query.filter(
                    models.Sample.id == proteomics_item["sample_id"]
                ).one()

                project_id = sample.condition.experiment.project_id
                
                if project_id not in verified_project_ids:
                    jwt_require_claim(project_id, "write")
                    verified_project_ids.add(project_id)

                proteomics.append(
                    models.Proteomics(
                        sample=sample,
                        identifier=proteomics_item["identifier"],
                        name=proteomics_item["name"],
                        full_name=proteomics_item["full_name"],
                        gene=proteomics_item["gene"],
                        measurement=proteomics_item["measurement"],
                        uncertainty=proteomics_item["uncertainty"],
                    )
                )
            except NoResultFound:
                abort(
                    404, f"Related object {proteomics_item['sample_id']} does not exist"
                )
        db.session.add_all(proteomics)
        db.session.commit()
        return (proteomics, 201)


class Proteomic(MethodResource):
    @marshal_with(schemas.Proteomics, 200)
    def get(self, id):
        try:
            return (
                models.Proteomics.query.filter(models.Proteomics.id == id)
                .filter(
                    models.Proteomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.Proteomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.Proteomics(exclude=("id",), partial=True))
    @marshal_with(schemas.Proteomics(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            proteomics = (
                models.Proteomics.query.filter(models.Proteomics.id == id)
                .filter(
                    models.Proteomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                proteomics.sample.condition.experiment.project_id, "write"
            )
            for field, value in payload.items():
                setattr(proteomics, field, value)
            db.session.add(proteomics)
            db.session.commit()
            return (proteomics, 200)

    @jwt_required
    def delete(self, id):
        try:
            proteomics = (
                models.Proteomics.query.filter(models.Proteomics.id == id)
                .filter(
                    models.Proteomics.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                proteomics.sample.condition.experiment.project_id, "admin"
            )
            db.session.delete(proteomics)
            db.session.commit()
            return make_response("", 204)


class UptakeSecretionRates(MethodResource):
    @marshal_with(schemas.UptakeSecretionRates(many=True), 200)
    def get(self):
        return models.UptakeSecretionRates.query.filter(
            models.UptakeSecretionRates.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.UptakeSecretionRates.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.UptakeSecretionRates(exclude=("id",)))
    @marshal_with(schemas.UptakeSecretionRates(only=("id",)), 201)
    def post(
        self,
        sample_id,
        compound_name,
        compound_identifier,
        compound_namespace,
        measurement,
        uncertainty,
    ):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        uptake_secretion_rate = models.UptakeSecretionRates(
            sample=sample,
            compound_name=compound_name,
            compound_identifier=compound_identifier,
            compound_namespace=compound_namespace,
            measurement=measurement,
            uncertainty=uncertainty,
        )
        db.session.add(uptake_secretion_rate)
        db.session.commit()
        return (uptake_secretion_rate, 201)


class UptakeSecretionRate(MethodResource):
    @marshal_with(schemas.UptakeSecretionRates, 200)
    def get(self, id):
        try:
            return (
                models.UptakeSecretionRates.query.filter(
                    models.UptakeSecretionRates.id == id
                )
                .filter(
                    models.UptakeSecretionRates.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.UptakeSecretionRates.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.UptakeSecretionRates(exclude=("id",), partial=True))
    @marshal_with(schemas.UptakeSecretionRates(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            uptake_secretion_rate = (
                models.UptakeSecretionRates.query.filter(
                    models.UptakeSecretionRates.id == id
                )
                .filter(
                    models.UptakeSecretionRates.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                uptake_secretion_rate.sample.condition.experiment.project_id, "write"
            )
            for field, value in payload.items():
                setattr(uptake_secretion_rate, field, value)
            db.session.add(uptake_secretion_rate)
            db.session.commit()
            return (uptake_secretion_rate, 200)

    @jwt_required
    def delete(self, id):
        try:
            uptake_secretion_rate = (
                models.UptakeSecretionRates.query.filter(
                    models.UptakeSecretionRates.id == id
                )
                .filter(
                    models.UptakeSecretionRates.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                uptake_secretion_rate.sample.condition.experiment.project_id, "admin"
            )
            db.session.delete(uptake_secretion_rate)
            db.session.commit()
            return make_response("", 204)


class MolarYields(MethodResource):
    @marshal_with(schemas.MolarYields(many=True), 200)
    def get(self):
        return models.MolarYields.query.filter(
            models.MolarYields.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.MolarYields.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.MolarYields(exclude=("id",)))
    @marshal_with(schemas.MolarYields(only=("id",)), 201)
    def post(
        self,
        sample_id,
        product_name,
        product_identifier,
        product_namespace,
        substrate_name,
        substrate_identifier,
        substrate_namespace,
        measurement,
        uncertainty,
    ):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        molar_yield = models.MolarYields(
            sample=sample,
            product_name=product_name,
            product_identifier=product_identifier,
            product_namespace=product_namespace,
            substrate_name=substrate_name,
            substrate_identifier=substrate_identifier,
            substrate_namespace=substrate_namespace,
            measurement=measurement,
            uncertainty=uncertainty,
        )
        db.session.add(molar_yield)
        db.session.commit()
        return (molar_yield, 201)


class MolarYield(MethodResource):
    @marshal_with(schemas.MolarYields, 200)
    def get(self, id):
        try:
            return (
                models.MolarYields.query.filter(models.MolarYields.id == id)
                .filter(
                    models.MolarYields.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.MolarYields.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.MolarYields(exclude=("id",), partial=True))
    @marshal_with(schemas.MolarYields(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            molar_yield = (
                models.MolarYields.query.filter(models.MolarYields.id == id)
                .filter(
                    models.MolarYields.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                molar_yield.sample.condition.experiment.project_id, "write"
            )
            for field, value in payload.items():
                setattr(molar_yield, field, value)
            db.session.add(molar_yield)
            db.session.commit()
            return (molar_yield, 200)

    @jwt_required
    def delete(self, id):
        try:
            molar_yield = (
                models.MolarYields.query.filter(models.MolarYields.id == id)
                .filter(
                    models.MolarYields.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                molar_yield.sample.condition.experiment.project_id, "admin"
            )
            db.session.delete(molar_yield)
            db.session.commit()
            return make_response("", 204)


class GrowthRates(MethodResource):
    @marshal_with(schemas.GrowthRate(many=True), 200)
    def get(self):
        return models.Growth.query.filter(
            models.Growth.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    )
                )
            )
            | models.Growth.sample.has(
                models.Sample.condition.has(
                    models.Condition.experiment.has(
                        models.Experiment.project_id.is_(None)
                    )
                )
            )
        ).all()

    @jwt_required
    @use_kwargs(schemas.GrowthRate(exclude=("id",)))
    @marshal_with(schemas.GrowthRate(only=("id",)), 201)
    def post(self, sample_id, measurement, uncertainty):
        try:
            sample = models.Sample.query.filter(models.Sample.id == sample_id).one()
            jwt_require_claim(sample.condition.experiment.project_id, "write")
        except NoResultFound:
            abort(404, f"Related object {sample_id} does not exist")
        growth_rate = models.Growth(
            sample=sample, measurement=measurement, uncertainty=uncertainty
        )
        db.session.add(growth_rate)
        db.session.commit()
        return (growth_rate, 201)


class GrowthRate(MethodResource):
    @marshal_with(schemas.GrowthRate, 200)
    def get(self, id):
        try:
            return (
                models.Growth.query.filter(models.Growth.id == id)
                .filter(
                    models.Growth.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                    | models.Growth.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.is_(None)
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")

    @jwt_required
    @use_kwargs(schemas.GrowthRate(exclude=("id",), partial=True))
    @marshal_with(schemas.GrowthRate(only=("id",)), 200)
    def put(self, id, **payload):
        try:
            growth_rate = (
                models.Growth.query.filter(models.Growth.id == id)
                .filter(
                    models.Growth.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                growth_rate.sample.condition.experiment.project_id, "write"
            )
            for field, value in payload.items():
                setattr(growth_rate, field, value)
            db.session.add(growth_rate)
            db.session.commit()
            return (growth_rate, 200)

    @jwt_required
    def delete(self, id):
        try:
            growth_rate = (
                models.Growth.query.filter(models.Growth.id == id)
                .filter(
                    models.Growth.sample.has(
                        models.Sample.condition.has(
                            models.Condition.experiment.has(
                                models.Experiment.project_id.in_(g.jwt_claims["prj"])
                            )
                        )
                    )
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(
                growth_rate.sample.condition.experiment.project_id, "admin"
            )
            db.session.delete(growth_rate)
            db.session.commit()
            return make_response("", 204)
