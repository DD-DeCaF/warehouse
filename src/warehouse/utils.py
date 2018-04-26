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

from flask_jwt_extended import get_jwt_claims

from warehouse.app import app, api, db, jwt


def filter_by_jwt_claims(model):
    projects = get_jwt_claims().get('prj', [])
    return filter_by_projects(model, projects)


def filter_by_projects(model, projects):
    return model.query.filter(model.project_id.in_(projects) | model.project_id.is_(None))


def get_object(model, object_id):
    obj = filter_by_jwt_claims(model).filter_by(id=object_id).first()
    if obj is None:
        api.abort(404, "{} {} doesn't exist".format(model, object_id))
    return obj


class CRUD(object):
    @classmethod
    def get_query(cls, model):
        return filter_by_jwt_claims(model)

    @classmethod
    def get(cls, model):
        return cls.get_query(model).all()

    @classmethod
    def post(cls, model):
        obj = model(**api.payload)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def get_by_id(cls, model, id):
        return get_object(model, id)

    @classmethod
    def delete(cls, model, id):
        obj = get_object(model, id)
        db.session.delete(obj)
        db.session.commit()

    @classmethod
    def put(cls, model, id):
        obj = get_object(model, id)
        for field in api.payload:
            if field != 'id' and field != 'project_id':
                obj[field] = api.payload[field]
        db.session.merge(obj)
        db.session.commit()
