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

from sqlalchemy import Integer, cast

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
    assert response.status_code == 200
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
    assert response.status_code == 200
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
    assert response.status_code == 200
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


def test_post_proteomics(client, tokens, session, data_fixtures):
    proteomics_request = {
        "sample_id": data_fixtures["sample"].id,
        "identifier": "P12345",
        "name": "AATM_RABIT",
        "full_name": "Aspartate aminotransferase, mitochondrial",
        "gene": "GOT2",
        "measurement": 0.1,
        "uncertainty": 0,
    }
    response = client.post(
        "/proteomics",
        headers={"Authorization": f"Bearer {tokens['write']}"},
        json=proteomics_request,
    )
    assert response.status_code == 201

    # Check that database entry matches posted data
    proteomics = models.Proteomics.query.filter(
        models.Proteomics.id == response.json["id"]
    ).one()
    assert proteomics.full_name == proteomics_request["full_name"]


def test_batch_post_proteomics(client, tokens, session, data_fixtures):
    item_count = 100
    proteomics_request = {
        "body": [
            {
                "sample_id": data_fixtures["sample"].id,
                "identifier": str(i),
                "name": "AATM_RABIT",
                "full_name": "Aspartate aminotransferase, mitochondrial",
                "gene": "GOT2",
                "measurement": 0.1,
                "uncertainty": 0,
            } for i in range(item_count)
        ]
    }
    response = client.post(
        "/proteomics/batch",
        headers={"Authorization": f"Bearer {tokens['write']}"},
        json=proteomics_request,
    )
    assert response.status_code == 201

    # Check that database entries match posted data
    proteomics_ids = set([data["id"] for data in response.json])
    proteomics = models.Proteomics.query.filter(
        models.Proteomics.id.in_(proteomics_ids)).order_by(
            cast(models.Proteomics.identifier, Integer)).all()
    for i in range(item_count):
        assert proteomics[i].identifier == proteomics_request["body"][i]["identifier"]


def test_batch_post_fluxomics(client, tokens, session, data_fixtures):
    item_count = 100
    fluxomics_request = {
        "body": [
            {
                "sample_id": data_fixtures["sample"].id,
                "reaction_name": "5-glutamyl-10FTHF transport, lysosomal",
                "reaction_identifier": str(i),
                "reaction_namespace": "metanetx.reaction",
                "measurement": 0.1,
                "uncertainty": 0,
            } for i in range(item_count)
        ]
    }
    response = client.post(
        "/fluxomics/batch",
        headers={"Authorization": f"Bearer {tokens['write']}"},
        json=fluxomics_request,
    )
    assert response.status_code == 201

    # Check that database entries match posted data
    fluxomics_ids = set([data["id"] for data in response.json])
    fluxomics = models.Fluxomics.query.filter(
        models.Fluxomics.id.in_(fluxomics_ids)).order_by(
            cast(models.Fluxomics.reaction_identifier, Integer)).all()
    for i in range(item_count):
        assert (fluxomics[i].reaction_identifier
                == fluxomics_request["body"][i]["reaction_identifier"])


def test_batch_post_metabolomics(client, tokens, session, data_fixtures):
    item_count = 100
    metabolomics_request = {
        "body": [
            {
                "sample_id": data_fixtures["sample"].id,
                "compound_name": "H(+)",
                "compound_identifier": str(i),
                "compound_namespace": "metanetx.chemical",
                "measurement": 0.1,
                "uncertainty": 0,
            } for i in range(item_count)
        ]
    }
    response = client.post(
        "/metabolomics/batch",
        headers={"Authorization": f"Bearer {tokens['write']}"},
        json=metabolomics_request,
    )
    assert response.status_code == 201

    # Check that database entries match posted data
    metabolomics_ids = set([data["id"] for data in response.json])
    metabolomics = models.Metabolomics.query.filter(
        models.Metabolomics.id.in_(metabolomics_ids)).order_by(
            cast(models.Metabolomics.compound_identifier, Integer)).all()
    for i in range(item_count):
        assert (metabolomics[i].compound_identifier
                == metabolomics_request["body"][i]["compound_identifier"])
