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


class StrictSchema(Schema):
    class Meta:
        strict = True


class Base(StrictSchema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.String(required=True)
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)


class Organism(Base):
  pass


class Namespace(Base):
  pass


class BiologicalEntityType(Base):
  pass


class Unit(Base):
  pass


class Experiment(Base):
    description = fields.String(required=True)


class Strain(Base):
    parent_id = fields.Integer(required=True)
    genotype = fields.String(required=True)
    organism_id = fields.Integer(required=True)


class BiologicalEntity(Base):
    namespace_id = fields.Integer(required=True)
    reference = fields.String(required=True)
    type_id = fields.Integer(required=True)


class MediumCompound(BiologicalEntity):
    mass_concentration = fields.Float(required=True)


class MediumCompoundSimple(StrictSchema):
    id = fields.Integer(required=True)
    mass_concentration = fields.Float(required=True)


class Medium(Base):
    ph = fields.Float(required=True)
    compounds = fields.List(fields.Nested(MediumCompound))


class MediumSimple(Base):
    ph = fields.Float(required=True)
    compounds = fields.List(fields.Nested(MediumCompoundSimple))


class Condition(StrictSchema):
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)
    id = fields.Integer(required=True)
    experiment_id = fields.Integer(required=True)
    name = fields.String(required=True)
    protocol = fields.String(required=True)
    temperature = fields.Float(required=True)
    aerobic = fields.Boolean(required=True)
    extra_data = fields.Raw(
        title='User-defined Extra Data',
        description='Field to allow users to add untyped metadata specific to '
                    'each condition',
        required=False, readonly=False,
        example="{'Stirrer Speed' : '300RPM', 'PH' : '7.9'}"
    ),
    strain_id = fields.Integer(required=True)
    medium_id = fields.Integer(required=True)
    feed_medium_id = fields.Integer(required=True)


class Sample(StrictSchema):
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)
    id = fields.Integer(required=True)
    condition_id = fields.Integer(required=True)
    datetime_start = fields.DateTime(required=True)
    datetime_end = fields.DateTime(required=True)
    numerator_id = fields.Integer(required=True)
    denominator_id = fields.Integer(required=True)
    value = fields.Float(required=True)
    unit_id = fields.Integer(required=True)
