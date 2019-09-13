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


class Organism(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.String(required=True)


class Strain(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.String(required=True)
    parent_id = fields.Integer(required=True, allow_none=True)
    genotype = fields.String(required=True)
    organism_id = fields.Integer(required=True)


class Experiment(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=True)


class Medium(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    name = fields.String(required=True)


class MediumCompound(Schema):
    id = fields.Integer(required=True)
    medium_id = fields.Integer(required=True)
    compound_name = fields.String(required=True)
    compound_identifier = fields.String(required=True)
    compound_namespace = fields.String(required=True)
    mass_concentration = fields.Float(required=True, allow_none=True)  # unit: mmol/l


class Condition(Schema):
    id = fields.Integer(required=True)
    experiment_id = fields.Integer(required=True)
    strain_id = fields.Integer(required=True)
    medium_id = fields.Integer(required=True)
    name = fields.String(required=True)


class Sample(Schema):
    id = fields.Integer(required=True)
    condition_id = fields.Integer(required=True)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True, allow_none=True)


class Fluxomics(Schema):
    id = fields.Integer(required=True)
    sample_id = fields.Integer(required=True)
    reaction_name = fields.String(required=True)
    reaction_identifier = fields.String(required=True)
    reaction_namespace = fields.String(required=True)
    measurement = fields.Float(required=True)  # unit: mmol/gDW/h
    uncertainty = fields.Float(required=True, allow_none=True)  # unit: mmol/gDW/h


class Metabolomics(Schema):
    id = fields.Integer(required=True)
    sample_id = fields.Integer(required=True)
    compound_name = fields.String(required=True)
    compound_identifier = fields.String(required=True)
    compound_namespace = fields.String(required=True)
    measurement = fields.Float(required=True)  # unit: mmol/l
    uncertainty = fields.Float(required=True, allow_none=True)  # unit: mmol/l


class UptakeSecretionRates(Schema):
    id = fields.Integer(required=True)
    sample_id = fields.Integer(required=True)
    compound_name = fields.String(required=True)
    compound_identifier = fields.String(required=True)
    compound_namespace = fields.String(required=True)
    measurement = fields.Float(required=True)  # unit: mmol/gDW/h
    uncertainty = fields.Float(required=True, allow_none=True)  # unit: mmol/gDW/h


class MolarYields(Schema):
    id = fields.Integer(required=True)
    sample_id = fields.Integer(required=True)
    product_name = fields.String(required=True)
    product_identifier = fields.String(required=True)
    product_namespace = fields.String(required=True)
    substrate_name = fields.String(required=True)
    substrate_identifier = fields.String(required=True)
    substrate_namespace = fields.String(required=True)
    # Both in mmol-product / mmol-substrate
    measurement = fields.Float(required=True)
    uncertainty = fields.Float(required=True, allow_none=True)


class GrowthRate(Schema):
    id = fields.Integer(required=True)
    sample_id = fields.Integer(required=True)
    measurement = fields.Float(required=True)  # unit: 1/h
    # unit: 1/h; 0 if no uncertainty or unknown
    uncertainty = fields.Float(required=True)


class ConditionData(Schema):
    class NestedMedium(Medium):
        compounds = fields.Nested(MediumCompound, many=True, required=True)

    class NestedSample(Sample):
        fluxomics = fields.Nested(Fluxomics, many=True, required=True)
        metabolomics = fields.Nested(Metabolomics, many=True, required=True)
        uptake_secretion_rates = fields.Nested(
            UptakeSecretionRates, many=True, required=True
        )
        molar_yields = fields.Nested(MolarYields, many=True, required=True)
        growth_rate = fields.Nested(GrowthRate, required=True)

    id = fields.Integer(required=True)
    experiment = fields.Nested(Experiment, required=True)
    strain = fields.Nested(Strain, required=True)
    medium = fields.Nested(NestedMedium, required=True)
    name = fields.String(required=True)
    samples = fields.Nested(NestedSample, many=True, required=True)
