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

from sqlalchemy.dialects import postgresql

from warehouse.app import db


class TimestampMixin(object):
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)


class Organism(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)

    name = db.Column(db.String(256), nullable=False)


class Strain(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)

    organism_id = db.Column(
        db.Integer,
        db.ForeignKey("organism.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    organism = db.relationship(Organism)

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("strain.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    parent = db.relationship("Strain", uselist=False)

    name = db.Column(db.String(256), nullable=False)
    genotype = db.Column(db.Text())


class Experiment(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)

    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text(), nullable=False)


class Medium(TimestampMixin, db.Model):
    project_id = db.Column(db.Integer)
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(256), nullable=False)


class MediumCompound(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    medium_id = db.Column(
        db.Integer,
        db.ForeignKey("medium.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    medium = db.relationship(
        Medium,
        backref=db.backref(
            "compounds", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    compound_name = db.Column(db.Text())
    compound_identifier = db.Column(db.Text())
    compound_namespace = db.Column(db.Text())
    mass_concentration = db.Column(db.Float())  # unit: mmol/l


class Condition(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    experiment_id = db.Column(
        db.Integer,
        db.ForeignKey("experiment.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    experiment = db.relationship(
        Experiment,
        backref=db.backref(
            "conditions", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    strain_id = db.Column(
        db.Integer,
        db.ForeignKey("strain.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    strain = db.relationship(Strain)

    medium_id = db.Column(
        db.Integer,
        db.ForeignKey("medium.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    medium = db.relationship(Medium, foreign_keys=[medium_id])

    name = db.Column(db.String(256), nullable=False)


class Sample(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    condition_id = db.Column(
        db.Integer,
        db.ForeignKey("condition.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    condition = db.relationship(
        Condition,
        backref=db.backref(
            "samples", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    name = db.Column(db.Text(), nullable=False)

    # Datetime fields for when the sample was taken. `end_time` is optional, used for
    # interval measurements like uptake rates or fluxomics.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)


class Fluxomics(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "fluxomics", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    reaction_name = db.Column(db.Text(), nullable=False)
    reaction_identifier = db.Column(db.Text(), nullable=False)
    reaction_namespace = db.Column(db.Text(), nullable=False)

    measurement = db.Column(db.Float, nullable=False)  # unit: mmol/gDW/h
    uncertainty = db.Column(db.Float, nullable=True)  # unit: mmol/gDW/h


class Metabolomics(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "metabolomics", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    compound_name = db.Column(db.Text(), nullable=False)
    compound_identifier = db.Column(db.Text(), nullable=False)
    compound_namespace = db.Column(db.Text(), nullable=False)

    measurement = db.Column(db.Float, nullable=False)  # unit: mmol/l
    uncertainty = db.Column(db.Float, nullable=True)  # unit: mmol/l


class UptakeSecretionRates(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "uptake_secretion_rates",
            cascade="all, delete-orphan",
            lazy="dynamic",
        ),
    )

    compound_name = db.Column(db.Text(), nullable=False)
    compound_identifier = db.Column(db.Text(), nullable=False)
    compound_namespace = db.Column(db.Text(), nullable=False)

    measurement = db.Column(db.Float, nullable=False)  # unit: mmol/gDW/h
    uncertainty = db.Column(db.Float, nullable=True)  # unit: mmol/gDW/h


class Proteomics(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "proteomics", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    identifier = db.Column(db.Text(), nullable=False)
    name = db.Column(db.Text(), nullable=False)
    full_name = db.Column(db.Text(), nullable=False)
    gene = db.Column(postgresql.JSON, nullable=False)

    measurement = db.Column(db.Float, nullable=False)  # unit: mmol/gDW
    uncertainty = db.Column(db.Float, nullable=True)  # unit: mmol/gDW


class MolarYields(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "molar_yields", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )

    product_name = db.Column(db.Text(), nullable=False)
    product_identifier = db.Column(db.Text(), nullable=False)
    product_namespace = db.Column(db.Text(), nullable=False)

    substrate_name = db.Column(db.Text(), nullable=False)
    substrate_identifier = db.Column(db.Text(), nullable=False)
    substrate_namespace = db.Column(db.Text(), nullable=False)

    # Both in mmol-product / mmol-substrate
    measurement = db.Column(db.Float, nullable=False)
    uncertainty = db.Column(db.Float, nullable=True)


class Growth(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sample_id = db.Column(
        db.Integer,
        db.ForeignKey("sample.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sample = db.relationship(
        Sample,
        backref=db.backref(
            "growth_rate",
            uselist=False,
            cascade="all, delete-orphan",
            lazy="select",
        ),
    )

    measurement = db.Column(db.Float, nullable=False)  # unit: 1/h
    # unit: 1/h; 0 if no uncertainty or unknown
    uncertainty = db.Column(db.Float, nullable=False)
