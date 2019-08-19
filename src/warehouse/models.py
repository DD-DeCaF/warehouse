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

from datetime import datetime

from warehouse.app import db


class TimestampMixin(object):
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)


class Organism(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class Strain(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    parent_id = db.Column(db.Integer, db.ForeignKey("strain.id"))
    parent = db.relationship("Strain")

    genotype = db.Column(db.Text())

    organism_id = db.Column(db.Integer, db.ForeignKey("organism.id"), nullable=False)
    organism = db.relationship(Organism)


class Medium(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    ph = db.Column(db.Float, nullable=False)

    compounds = db.relationship("BiologicalEntity", secondary="medium_compound")


class Namespace(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class BiologicalEntityType(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class BiologicalEntity(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(2048), nullable=False)

    namespace_id = db.Column(db.Integer, db.ForeignKey("namespace.id"), nullable=False)
    namespace = db.relationship(Namespace)

    reference = db.Column(db.String(256), nullable=False)

    type_id = db.Column(
        db.Integer, db.ForeignKey("biological_entity_type.id"), nullable=False
    )
    type = db.relationship(BiologicalEntityType)


class MediumCompound(TimestampMixin, db.Model):
    __table_args__ = (db.PrimaryKeyConstraint("medium_id", "compound_id"),)

    __mapper_args__ = {"confirm_deleted_rows": False}

    medium_id = db.Column(db.Integer, db.ForeignKey("medium.id"))
    compound_id = db.Column(db.Integer, db.ForeignKey("biological_entity.id"))
    mass_concentration = db.Column(db.Float)

    medium = db.relationship(
        Medium,
        backref=db.backref("composition", cascade="all, delete-orphan", lazy="dynamic"),
    )
    compound = db.relationship(BiologicalEntity)


class Unit(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)


class Experiment(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    description = db.Column(db.Text(), nullable=False)


# TODO: tags
# TODO: info to put to columns (protocol, temperature, gas etc)
class Condition(TimestampMixin, db.Model):
    experiment_id = db.Column(
        db.Integer, db.ForeignKey("experiment.id"), nullable=False
    )
    experiment = db.relationship(
        Experiment,
        backref=db.backref("conditions", cascade="all, delete-orphan", lazy="dynamic"),
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    protocol = db.Column(db.String(256))
    temperature = db.Column(db.Float, nullable=False)
    aerobic = db.Column(db.Boolean, nullable=False)
    extra_data = db.Column(db.JSON, nullable=True)

    strain_id = db.Column(db.Integer, db.ForeignKey("strain.id"), nullable=False)
    strain = db.relationship(Strain)

    medium_id = db.Column(db.Integer, db.ForeignKey("medium.id"), nullable=False)
    medium = db.relationship(Medium, foreign_keys=[medium_id])

    feed_medium_id = db.Column(db.Integer, db.ForeignKey("medium.id"))
    feed_medium = db.relationship(Medium, foreign_keys=[feed_medium_id])


class Sample(TimestampMixin, db.Model):
    condition_id = db.Column(db.Integer, db.ForeignKey("condition.id"), nullable=False)
    condition = db.relationship(
        Condition,
        backref=db.backref("samples", cascade="all, delete-orphan", lazy="dynamic"),
    )

    id = db.Column(db.Integer, primary_key=True)

    datetime_start = db.Column(db.DateTime, nullable=False)
    datetime_end = db.Column(db.DateTime)

    numerator_id = db.Column(db.Integer, db.ForeignKey("biological_entity.id"))
    numerator = db.relationship(BiologicalEntity, foreign_keys=[numerator_id])

    denominator_id = db.Column(db.Integer, db.ForeignKey("biological_entity.id"))
    denominator = db.relationship(BiologicalEntity, foreign_keys=[denominator_id])

    value = db.Column(db.Float, nullable=False)

    unit_id = db.Column(db.Integer, db.ForeignKey("unit.id"), nullable=False)
    unit = db.relationship(Unit)

    def is_growth_rate(self):
        return (
            self.numerator is None
            and self.denominator is None
            and self.unit.name == "growth (1/h)"
        )

    def is_fluxomics(self):
        return (
            self.numerator is not None
            and self.numerator.type.name == "reaction"
            and self.denominator is None
        )

    def is_metabolomics(self):
        return (
            self.numerator is not None
            and self.numerator.type.name == "compound"
            and self.denominator is None
            and self.unit.name == "compound / CDW (mmol/g/h)"
        )
