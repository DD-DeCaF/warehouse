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

"""
Test the CRUD endpoints in a repetitive fashion.

A test performs a single HTTP request against one of the CRUD endpoints. Expect to see
GET, POST for list endpoints, then GET, PUT, DELETE for item endpoints, repeated for
each resource type.
"""

from warehouse import models


def test_get_organisms(client, tokens, session, data_fixtures):
    response = client.get(
        "/organisms", headers={"Authorization": f"Bearer {tokens['read']}"}
    )
    assert response.status_code == 200


def test_post_organism(client, tokens, session):
    response = client.post(
        "/organisms",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"project_id": 1, "name": "E. coli"},
    )
    assert response.status_code == 201


def test_get_organism(client, tokens, session, data_fixtures):
    response = client.get(
        f"/organisms/{data_fixtures['organism'].id}",
        headers={"Authorization": f"Bearer {tokens['read']}"},
    )
    assert response.status_code == 200


def test_put_organism(client, tokens, session, data_fixtures):
    response = client.put(
        f"/organisms/{data_fixtures['organism'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"name": "Modified"},
    )
    assert response.status_code == 204
    organism = models.Organism.query.filter(
        models.Organism.id == data_fixtures["organism"].id
    ).one()
    assert organism.name == "Modified"


def test_delete_organism(client, tokens, session, data_fixtures):
    response = client.delete(
        f"/organisms/{data_fixtures['organism'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    assert response.status_code == 204
    assert (
        models.Organism.query.filter(
            models.Organism.id == data_fixtures["organism"].id
        ).count()
        == 0
    )


def test_get_strains(client, tokens, session, data_fixtures):
    response = client.get(
        "/strains", headers={"Authorization": f"Bearer {tokens['read']}"}
    )
    assert response.status_code == 200


def test_post_strain(client, tokens, session, data_fixtures):
    response = client.post(
        "/strains",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "project_id": 1,
            "organism_id": data_fixtures["organism"].id,
            "parent_id": None,
            "name": "Strain example",
            "genotype": "Some genotype",
        },
    )
    assert response.status_code == 201


def test_get_strain(client, tokens, session, data_fixtures):
    response = client.get(
        f"/strains/{data_fixtures['strain'].id}",
        headers={"Authorization": f"Bearer {tokens['read']}"},
    )
    assert response.status_code == 200


def test_put_strain(client, tokens, session, data_fixtures):
    response = client.put(
        f"/strains/{data_fixtures['strain'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"name": "Modified"},
    )
    assert response.status_code == 204
    strain = models.Strain.query.filter(
        models.Strain.id == data_fixtures["strain"].id
    ).one()
    assert strain.name == "Modified"


def test_delete_strain(client, tokens, session, data_fixtures):
    response = client.delete(
        f"/strains/{data_fixtures['strain'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    assert response.status_code == 204
    assert (
        models.Strain.query.filter(
            models.Strain.id == data_fixtures["strain"].id
        ).count()
        == 0
    )


def test_get_experiments(client, tokens, session, data_fixtures):
    response = client.get(
        "/experiments", headers={"Authorization": f"Bearer {tokens['read']}"}
    )
    assert response.status_code == 200


def test_post_experiment(client, tokens, session, data_fixtures):
    response = client.post(
        "/experiments",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "project_id": 1,
            "name": "Experiment example",
            "description": "Some description",
        },
    )
    assert response.status_code == 201


def test_get_experiment(client, tokens, session, data_fixtures):
    response = client.get(
        f"/experiments/{data_fixtures['experiment'].id}",
        headers={"Authorization": f"Bearer {tokens['read']}"},
    )
    assert response.status_code == 200


def test_put_experiment(client, tokens, session, data_fixtures):
    response = client.put(
        f"/experiments/{data_fixtures['experiment'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"name": "Modified"},
    )
    assert response.status_code == 204
    experiment = models.Experiment.query.filter(
        models.Experiment.id == data_fixtures["experiment"].id
    ).one()
    assert experiment.name == "Modified"


def test_delete_experiment(client, tokens, session, data_fixtures):
    response = client.delete(
        f"/experiments/{data_fixtures['experiment'].id}",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    assert response.status_code == 204
    assert (
        models.Experiment.query.filter(
            models.Experiment.id == data_fixtures["experiment"].id
        ).count()
        == 0
    )
