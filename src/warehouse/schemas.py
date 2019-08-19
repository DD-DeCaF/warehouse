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

from marshmallow import Schema, fields
from marshmallow.validate import OneOf


class StrictSchema(Schema):
    class Meta:
        strict = True


class Base(StrictSchema):
    id = fields.Integer(allow_none=True)
    project_id = fields.Integer(allow_none=True)
    name = fields.String(allow_none=True)
    created = fields.DateTime(allow_none=True)
    updated = fields.DateTime(allow_none=True)


class Organism(Base):
    pass


class Namespace(Base):
    pass


class BiologicalEntityType(Base):
    pass


class Unit(Base):
    pass


class Experiment(Base):
    description = fields.String(allow_none=True)


class Strain(Base):
    parent_id = fields.Integer(allow_none=True)
    genotype = fields.String(allow_none=True)
    organism_id = fields.Integer(allow_none=True)


class BiologicalEntity(Base):
    namespace_id = fields.Integer(allow_none=True)
    reference = fields.String(allow_none=True)
    type_id = fields.Integer(allow_none=True)


class MediumCompound(BiologicalEntity):
    mass_concentration = fields.Float(allow_none=True)


class MediumCompoundSimple(StrictSchema):
    id = fields.Integer(allow_none=True)
    mass_concentration = fields.Float(allow_none=True)


class Medium(Base):
    ph = fields.Float(allow_none=True)
    compounds = fields.List(fields.Nested(MediumCompound))


class MediumSimple(Base):
    ph = fields.Float(allow_none=True)
    compounds = fields.List(fields.Nested(MediumCompoundSimple))


class Condition(StrictSchema):
    created = fields.DateTime(allow_none=True)
    updated = fields.DateTime(allow_none=True)
    id = fields.Integer(allow_none=True)
    experiment_id = fields.Integer(allow_none=True)
    name = fields.String(allow_none=True)
    protocol = fields.String(allow_none=True)
    temperature = fields.Float(allow_none=True)
    aerobic = fields.Boolean(allow_none=True)
    extra_data = (
        fields.Raw(
            title="User-defined Extra Data",
            description="Field to allow users to add untyped metadata specific to "
            "each condition",
            required=False,
            example="{'Stirrer Speed' : '300RPM', 'PH' : '7.9'}",
        ),
    )
    strain_id = fields.Integer(allow_none=True)
    medium_id = fields.Integer(allow_none=True)
    feed_medium_id = fields.Integer(allow_none=True)


class Sample(StrictSchema):
    created = fields.DateTime(allow_none=True)
    updated = fields.DateTime(allow_none=True)
    id = fields.Integer(allow_none=True)
    condition_id = fields.Integer(allow_none=True)
    datetime_start = fields.DateTime(allow_none=True)
    datetime_end = fields.DateTime(allow_none=True)
    numerator_id = fields.Integer(allow_none=True)
    denominator_id = fields.Integer(allow_none=True)
    value = fields.Float(allow_none=True)
    unit_id = fields.Integer(allow_none=True)


class MediumCompoundData(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    # Note: namespace should match a namespace identifier from miriam.
    # See https://www.ebi.ac.uk/miriam/main/collections
    namespace = fields.String(required=True)


class Measurement(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    # Note: namespace should match a namespace identifier from miriam.
    # See https://www.ebi.ac.uk/miriam/main/collections
    namespace = fields.String(required=True)
    measurements = fields.List(fields.Float())
    type = fields.String(
        required=True, validate=OneOf(["compound", "reaction", "protein"])
    )


class GrowthRate(Schema):
    measurements = fields.List(fields.Float())


class ModelingData(Schema):
    medium = fields.Nested(MediumCompoundData, many=True, missing=None)
    genotype = fields.List(fields.String(), missing=None)
    growth_rate = fields.Nested(GrowthRate, missing=None)
    measurements = fields.Nested(Measurement, many=True, missing=None)
