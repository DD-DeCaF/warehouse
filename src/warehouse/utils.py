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

from flask import abort, g
from sqlalchemy.orm.exc import NoResultFound


def verify_relation(ModelClass, object_id):
    try:
        return (
            ModelClass.query.filter(ModelClass.id == object_id)
            .filter(
                ModelClass.project_id.in_(g.jwt_claims["prj"])
                | ModelClass.project_id.is_(None)
            )
            .one()
        )
    except NoResultFound:
        abort(404, f"Related object {object_id} does not exist")
