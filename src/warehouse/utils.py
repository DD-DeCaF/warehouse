from flask_jwt_extended import get_jwt_claims

from warehouse.app import app, api, db, jwt


def filter_by_jwt_claims(model):
    projects = get_jwt_claims().get('prj', [])
    return model.query.filter(model.project_id.in_(projects) | model.project_id.is_(None))


def get_object(model, object_id):
    obj = filter_by_jwt_claims(model.query).filter_by(id=object_id).first()
    if obj is None:
        api.abort(404, "{} {} doesn't exist".format(model, object_id))
    return obj


class CRUD(object):
    @classmethod
    def get(cls, model):
        return filter_by_jwt_claims(model).all()

    @classmethod
    def post(cls, model):
        app.logger.debug(api.payload)
        obj = model(**api.payload)
        app.logger.debug(obj)
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
