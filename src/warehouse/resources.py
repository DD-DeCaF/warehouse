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

from flask import abort, make_response, g
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
    @use_kwargs(schemas.Organism(exclude=("id",)))
    @marshal_with(schemas.Organism(only=("id",), partial=True), 204)
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
            return (organism, 204)

    @jwt_required
    def delete(self, id):
        try:
            organism = (
                models.Organism.query.filter(models.Organism.id == id)
                .filter(
                    models.Organism.project_id.in_(g.jwt_claims["prj"])
                    | models.Organism.project_id.is_(None)
                )
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
    @use_kwargs(schemas.Strain(exclude=("id",)))
    @marshal_with(schemas.Strain(only=("id",), partial=True), 204)
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
            return (strain, 204)

    @jwt_required
    def delete(self, id):
        try:
            strain = (
                models.Strain.query.filter(models.Strain.id == id)
                .filter(
                    models.Strain.project_id.in_(g.jwt_claims["prj"])
                    | models.Strain.project_id.is_(None)
                )
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
            project_id=project_id,
            name=name,
            description=description,
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
    @use_kwargs(schemas.Experiment(exclude=("id",)))
    @marshal_with(schemas.Experiment(only=("id",), partial=True), 204)
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
            return (experiment, 204)

    @jwt_required
    def delete(self, id):
        try:
            experiment = (
                models.Experiment.query.filter(models.Experiment.id == id)
                .filter(
                    models.Experiment.project_id.in_(g.jwt_claims["prj"])
                    | models.Experiment.project_id.is_(None)
                )
                .one()
            )
        except NoResultFound:
            abort(404, f"Cannot find object with id {id}")
        else:
            jwt_require_claim(experiment.project_id, "admin")
            db.session.delete(experiment)
            db.session.commit()
            return make_response("", 204)
