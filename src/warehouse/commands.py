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
import yaml
from flask_script import Manager

from warehouse.app import db, app
from warehouse.models import Strain, Organism, Namespace, BiologicalEntityType, BiologicalEntity, Medium, Unit, Experiment


Fixtures = Manager(usage="Populate the database with fixtures")


def add_from_file(filepath, model):
    objects = yaml.load(open(filepath, 'r'))
    for obj in objects:
        new_object = model(**obj)
        db.session.add(new_object)
        db.session.flush()
    db.session.commit()
    app.logger.debug('{} is added: {} objects in db'.format(model, model.query.count()))


@Fixtures.command
def organisms(filepath='fixtures/organisms.yaml'):
    add_from_file(filepath, Organism)


@Fixtures.command
def strains(filepath='fixtures/strains.yaml'):
    add_from_file(filepath, Strain)


@Fixtures.command
def namespaces(filepath='fixtures/namespaces.yaml'):
    add_from_file(filepath, Namespace)


@Fixtures.command
def types(filepath='fixtures/types.yaml'):
    add_from_file(filepath, BiologicalEntityType)


@Fixtures.command
def units(filepath='fixtures/units.yaml'):
    add_from_file(filepath, Unit)


@Fixtures.command
def biological_entities(filepath='fixtures/biological_entities.yaml'):
    add_from_file(filepath, BiologicalEntity)


@Fixtures.command
def experiments(filepath='fixtures/experiments.yaml'):
    add_from_file(filepath, Experiment)


@Fixtures.command
def media(filepath='fixtures/media.yaml'):
    objects = yaml.load(open(filepath, 'r'))
    for obj in objects:
        composition = dict(zip(obj['compounds'], obj['mass_concentrations']))
        medium = Medium(
            project_id=obj['project_id'],
            name=obj['name'],
            ph=obj['ph'],
        )
        medium.compounds = BiologicalEntity.query.filter(BiologicalEntity.id.in_(obj['compounds'])).all()
        db.session.add(medium)
        db.session.flush()
        app.logger.debug(medium.composition.all())
        for c in medium.composition:
            app.logger.debug(c)
            c.mass_concentration = composition[c.compound_id]
        db.session.flush()
    db.session.commit()


@Fixtures.command
def populate():
    units()
    types()
    namespaces()
    experiments()
    biological_entities()
    media()
    organisms()
    strains()

