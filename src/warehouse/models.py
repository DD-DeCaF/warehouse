# Copyright 2018 Novo Nordisk Foundation Center for Biosustainability, DTU.
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

from warehouse.app import db


class Organism(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class Strain(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    parent_id = db.Column(db.Integer, db.ForeignKey('strain.id'))
    parent = db.relationship('Strain')

    genotype = db.Column(db.Text())

    organism_id = db.Column(db.Integer, db.ForeignKey('organism.id'))
    organism = db.relationship(Organism)


class Medium(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    ph = db.Column(db.Float, nullable=False)

    compounds = db.relationship(
        "BiologicalEntity",
        secondary='medium_compound',
    )


class Namespace(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class BiologicalEntityType(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class BiologicalEntity(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    namespace_id = db.Column(db.Integer, db.ForeignKey('namespace.id'))
    namespace = db.relationship(Namespace)

    reference = db.Column(db.String(256), nullable=False)

    type_id = db.Column(db.Integer, db.ForeignKey('biological_entity_type.id'))
    type = db.relationship(BiologicalEntityType)


class MediumCompound(db.Model):
    __table_args__ = (
        db.PrimaryKeyConstraint('medium_id', 'compound_id'),
    )

    medium_id = db.Column(db.Integer, db.ForeignKey('medium.id'))
    compound_id = db.Column(db.Integer, db.ForeignKey('biological_entity.id'))
    mass_concentration = db.Column(db.Float)

    medium = db.relationship(Medium, backref=db.backref('composition', cascade="all, delete-orphan", lazy='dynamic'))
    compound = db.relationship(BiologicalEntity)


class Unit(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
