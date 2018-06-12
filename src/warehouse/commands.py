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
from flask_script import Manager

from warehouse.models import Strain, Organism, Namespace, BiologicalEntityType, BiologicalEntity, Medium, Unit, Experiment, Sample, Measurement
from warehouse.utils import add_from_file


Fixtures = Manager(usage="Populate the database with fixtures")


@Fixtures.command
def organisms(filepath='fixtures/organisms.yaml'):
    add_from_file(open(filepath, 'r'), Organism)


@Fixtures.command
def strains(filepath='fixtures/strains.yaml'):
    add_from_file(open(filepath, 'r'), Strain)


@Fixtures.command
def namespaces(filepath='fixtures/namespaces.yaml'):
    add_from_file(open(filepath, 'r'), Namespace)


@Fixtures.command
def types(filepath='fixtures/types.yaml'):
    add_from_file(open(filepath, 'r'), BiologicalEntityType)


@Fixtures.command
def units(filepath='fixtures/units.yaml'):
    add_from_file(open(filepath, 'r'), Unit)


@Fixtures.command
def biological_entities(filepath='fixtures/biological_entities.yaml'):
    add_from_file(open(filepath, 'r'), BiologicalEntity)


@Fixtures.command
def experiments(filepath='fixtures/experiments.yaml'):
    add_from_file(open(filepath, 'r'), Experiment)


@Fixtures.command
def samples(filepath='fixtures/samples.yaml'):
    add_from_file(open(filepath, 'r'), Sample)


@Fixtures.command
def measurements(filepath='fixtures/measurements.yaml'):
    add_from_file(open(filepath, 'r'), Measurement)


@Fixtures.command
def media(filepath='fixtures/media.yaml'):
    add_from_file(open(filepath, 'r'), Medium)


@Fixtures.command
def populate():
    units()
    types()
    namespaces()
    biological_entities()
    media()
    organisms()
    strains()
    experiments()
    samples()
    measurements()
