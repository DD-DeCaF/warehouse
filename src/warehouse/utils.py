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

import json
from flask_jwt_extended import get_jwt_claims
from sqlalchemy import exc
from warehouse.app import app, api, db, jwt
from warehouse.models import Sample, Experiment, Measurement, BiologicalEntity, Medium


def filter_by_jwt_claims(model):
    projects = get_jwt_claims().get('prj', [])
    return filter_by_projects(model, projects)


def filter_by_projects(model, projects):
    return model.query.filter(model.project_id.in_(projects) | model.project_id.is_(None))


def get_object(model, object_id):
    obj = filter_by_jwt_claims(model).filter_by(id=object_id).first()
    if obj is None:
        api.abort(404, "{} {} doesn't exist".format(model.__name__, object_id))
    return obj


def constraint_check(db):
    try:
        db.session.commit()
    except exc.IntegrityError:
        db.session.rollback()
        api.abort(409, "Wrong data")


def get_sample_by_id(sample_id):
    sample = Sample.query.get(sample_id)
    if sample is None:
        api.abort(404, "No such sample")
    query = filter_by_jwt_claims(Experiment).filter_by(id=sample.experiment.id)
    if not query.count():
        api.abort(404, "No such sample")
    return sample


def get_measurement_by_id(measurement_id):
    measurement = Measurement.query.get(measurement_id)
    if measurement is None:
        api.abort(404, "No such measurement")
    query = filter_by_jwt_claims(Experiment).filter_by(id=measurement.sample.experiment.id)
    if not query.count():
        api.abort(404, "No such measurement")
    return measurement


def add_from_file(file_object, model):
    if model.__tablename__ == 'medium':
        return add_media_from_file(file_object)
    app.logger.debug('Started loading the file')
    for line in file_object:
        obj = json.loads(line)
        new_object = model(**obj)
        db.session.add(new_object)
        db.session.flush()
    db.session.commit()
    app.logger.debug('{}: {} objects in db'.format(model, model.query.count()))


def add_media_from_file(file_object):
    for line in file_object:
        obj = json.loads(line)
        composition = dict(zip(obj['compounds'], obj['mass_concentrations']))
        medium_obj = dict(
            project_id=obj['project_id'],
            name=obj['name'],
            ph=obj['ph'],
        )
        if 'id' in obj:
            medium_obj['id'] = obj['id']
        medium = Medium(
            **medium_obj
        )
        medium.compounds = BiologicalEntity.query.filter(BiologicalEntity.id.in_(obj['compounds'])).all()
        db.session.add(medium)
        db.session.flush()
        for c in medium.composition:
            c.mass_concentration = composition[c.compound_id]
        db.session.flush()
    db.session.commit()
    app.logger.debug('Medium: added, {} objects in db'.format(Medium.query.count()))


class CRUD(object):
    @classmethod
    def get_query(cls, model):
        return filter_by_jwt_claims(model)

    @classmethod
    def get(cls, model):
        return cls.get_query(model).all()

    @classmethod
    def post(cls, data, model, check_permissions=None, project_id=True):
        if project_id:
            if data.get('project_id', None) is None:
                api.abort(403, 'Project ID is not set')
            else:
                obj = model(project_id=data['project_id'])
        else:
            obj = model()
        cls.modify_object(data, obj, check_permissions=check_permissions)
        db.session.add(obj)
        constraint_check(db)
        return obj

    @classmethod
    def get_by_id(cls, model, id):
        return get_object(model, id)

    @classmethod
    def delete(cls, model, id):
        obj = get_object(model, id)
        db.session.delete(obj)
        constraint_check(db)

    @classmethod
    def put(cls, data, model, id, check_permissions=None):
        obj = get_object(model, id)
        cls.modify_object(data, obj, check_permissions=check_permissions)
        db.session.merge(obj)
        constraint_check(db)
        return obj

    @classmethod
    def modify_object(cls, data, obj, check_permissions=None):
        if check_permissions is None:
            check_permissions = {}
        for field, new_value in data.items():
            if field in check_permissions and new_value is not None:
                if field == 'sample_id':
                    get_sample_by_id(new_value)
                else:
                    get_object(check_permissions[field], new_value)
            if field != 'id' and field != 'project_id':
                setattr(obj, field, new_value)
