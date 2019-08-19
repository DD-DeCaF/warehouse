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

from warehouse.models import (
    BiologicalEntity,
    BiologicalEntityType,
    Condition,
    Experiment,
    Medium,
    Namespace,
    Organism,
    Sample,
    Strain,
    Unit,
)
from warehouse.utils import add_from_file


Fixtures = Manager(usage="Populate the database with fixtures")


@Fixtures.command
def organisms(filepath="fixtures/organisms.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Organism)


@Fixtures.command
def strains(filepath="fixtures/strains.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Strain)


@Fixtures.command
def namespaces(filepath="fixtures/namespaces.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Namespace)


@Fixtures.command
def types(filepath="fixtures/types.json"):
    with open(filepath, "r") as f:
        add_from_file(f, BiologicalEntityType)


@Fixtures.command
def units(filepath="fixtures/units.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Unit)


@Fixtures.command
def biological_entities(filepath="fixtures/biological_entities.json"):
    with open(filepath, "r") as f:
        add_from_file(f, BiologicalEntity)


@Fixtures.command
def experiments(filepath="fixtures/experiments.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Experiment)


@Fixtures.command
def conditions(filepath="fixtures/conditions.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Condition)


@Fixtures.command
def samples(filepath="fixtures/samples.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Sample)


@Fixtures.command
def media(filepath="fixtures/media.json"):
    with open(filepath, "r") as f:
        add_from_file(f, Medium)


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
    conditions()
    samples()
