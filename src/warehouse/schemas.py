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
    id = fields.Integer()
    project_id = fields.Integer()
    name = fields.String()


class Strain(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    name = fields.String()
    parent_id = fields.Integer(allow_none=True)
    genotype = fields.String()
    organism_id = fields.Integer()


class Experiment(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    name = fields.String()
    description = fields.String()


class Medium(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    name = fields.String()


class MediumCompound(Schema):
    id = fields.Integer()
    medium_id = fields.Integer()
    compound_name = fields.String()
    compound_identifier = fields.String()
    compound_namespace = fields.String()
    mass_concentration = fields.Float(allow_none=True)  # unit: mmol/l


class Condition(Schema):
    id = fields.Integer()
    experiment_id = fields.Integer()
    strain_id = fields.Integer()
    medium_id = fields.Integer()
    name = fields.String()


class Sample(Schema):
    id = fields.Integer()
    condition_id = fields.Integer()
    start_time = fields.DateTime()
    end_time = fields.DateTime(allow_none=True)


class Fluxomics(Schema):
    id = fields.Integer()
    sample_id = fields.Integer()
    reaction_name = fields.String()
    reaction_identifier = fields.String()
    reaction_namespace = fields.String()
    measurement = fields.Float()  # unit: mmol/gDW/h
    uncertainty = fields.Float(allow_none=True)  # unit: mmol/gDW/h


class Metabolomics(Schema):
    id = fields.Integer()
    sample_id = fields.Integer()
    compound_name = fields.String()
    compound_identifier = fields.String()
    compound_namespace = fields.String()
    measurement = fields.Float()  # unit: mmol/l
    uncertainty = fields.Float(allow_none=True)  # unit: mmol/l


class UptakeSecretionRates(Schema):
    id = fields.Integer()
    sample_id = fields.Integer()
    compound_name = fields.String()
    compound_identifier = fields.String()
    compound_namespace = fields.String()
    measurement = fields.Float()  # unit: mmol/gDW/h
    uncertainty = fields.Float(allow_none=True)  # unit: mmol/gDW/h


class MolarYields(Schema):
    id = fields.Integer()
    sample_id = fields.Integer()
    product_name = fields.String()
    product_identifier = fields.String()
    product_namespace = fields.String()
    substrate_name = fields.String()
    substrate_identifier = fields.String()
    substrate_namespace = fields.String()
    # Both in mmol-product / mmol-substrate
    measurement = fields.Float()
    uncertainty = fields.Float(allow_none=True)


class GrowthRate(Schema):
    id = fields.Integer()
    sample_id = fields.Integer()
    measurement = fields.Float()  # unit: 1/h
    uncertainty = fields.Float()  # unit: 1/h; 0 if no uncertainty or unknown


class ConditionData(Schema):
    class NestedMedium(Medium):
        compounds = fields.Nested(MediumCompound, many=True)

    class NestedSample(Sample):
        fluxomics = fields.Nested(Fluxomics, many=True)
        metabolomics = fields.Nested(Metabolomics, many=True)
        uptake_secretion_rates = fields.Nested(UptakeSecretionRates, many=True)
        molar_yields = fields.Nested(MolarYields, many=True)
        growth_rate = fields.Nested(GrowthRate)

    id = fields.Integer()
    experiment = fields.Nested(Experiment)
    strain = fields.Nested(Strain)
    medium = fields.Nested(NestedMedium)
    name = fields.String()
    samples = fields.Nested(Sample)
