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
from warehouse.models import Strain


Fixtures = Manager(usage="Populate the database with fixtures")


@Fixtures.command
def strains(filepath='fixtures/strains.yaml'):
    strains = yaml.load(open(filepath, 'r'))
    for d in strains:
        strain = Strain(**d)
        db.session.add(strain)
        db.session.flush()
    db.session.commit()
    app.logger.debug('All strains is added: {} objects in db'.format(Strain.query.count()))
