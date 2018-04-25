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

"""Test utils"""

import pytest
import werkzeug
from warehouse import utils
from warehouse import models


def test_get_object():
    """If jwt is not available public objects should be returned, but private object should respond with 404"""
    public_object = utils.get_object(models.BiologicalEntityType, 1)
    assert public_object.project_id is None
    with pytest.raises(werkzeug.exceptions.NotFound):
        utils.get_object(models.BiologicalEntityType, 3)
        utils.get_object(models.BiologicalEntityType, 666)


def test_check_claims():
    """For the given list of project ids return all the objects belonging to the project and public objects"""
    assert utils.filter_by_projects(models.Namespace, [1]).count() == 4
    assert utils.filter_by_projects(models.Organism, [4]).count() == 3
    assert utils.filter_by_projects(models.Strain, []).count() == 1
