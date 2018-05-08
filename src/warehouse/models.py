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

    organism_id = db.Column(db.Integer, db.ForeignKey('organism.id'), nullable=False)
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

    namespace_id = db.Column(db.Integer, db.ForeignKey('namespace.id'), nullable=False)
    namespace = db.relationship(Namespace)

    reference = db.Column(db.String(256), nullable=False)

    type_id = db.Column(db.Integer, db.ForeignKey('biological_entity_type.id'), nullable=False)
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


class Experiment(db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    description = db.Column(db.Text(), nullable=False)


# TODO: tags
# TODO: info to put to columns (protocol, temperature, gas etc)
class Sample(db.Model):
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship(Experiment, backref=db.backref('samples', cascade="all, delete-orphan", lazy='dynamic'))

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    protocol = db.Column(db.String(256))
    temperature = db.Column(db.Float, nullable=False)
    gas = db.Column(db.String(256), nullable=False)  # TODO: enum for gases

    strain_id = db.Column(db.Integer, db.ForeignKey('strain.id'), nullable=False)
    strain = db.relationship(Strain)

    medium_id = db.Column(db.Integer, db.ForeignKey('medium.id'), nullable=False)
    medium = db.relationship(Medium)


class Measurement(db.Model):
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'), nullable=False)
    sample = db.relationship(Sample, backref=db.backref('measurements', cascade="all, delete-orphan", lazy='dynamic'))

    id = db.Column(db.Integer, primary_key=True)

    datetime_start = db.Column(db.DateTime, nullable=False)
    datetime_end = db.Column(db.DateTime)

    numerator_id = db.Column(db.Integer, db.ForeignKey('biological_entity.id'), nullable=False)
    numerator = db.relationship(BiologicalEntity, foreign_keys=[numerator_id])

    denominator_id = db.Column(db.Integer, db.ForeignKey('biological_entity.id'))
    denominator = db.relationship(BiologicalEntity, foreign_keys=[denominator_id])

    value = db.Column(db.Float, nullable=False)

    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    unit = db.relationship(Unit)
