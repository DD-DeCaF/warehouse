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

"""Test expected functioning of the OpenAPI docs endpoints."""

import json
from pytest import mark


ENDPOINTS = [
    '/strains',
    '/units',
    '/bioentities',
    '/namespaces',
    '/organisms',
    '/types',
    '/media',
]


POST_SIMPLE = [
    ('/units', {'name': 'mmol'}),
    ('/namespaces', {'name': 'new namespace'}),
    ('/organisms', {'name': 'mouse'}),
    ('/types', {'name': 'protein'}),
    ('/strains', {'name': 'strain', 'genotype': '', 'parent_id': None, 'organism_id': 1}),
    ('/bioentities', {'name': 'reaction1', 'namespace_id': 1, 'reference': '666', 'type_id': 1}),
]


def test_docs(client):
    """Expect the OpenAPI docs to be served at root."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.content_type == "text/html; charset=utf-8"


@mark.parametrize('endpoint', ENDPOINTS)
def test_get_all(client, tokens, endpoint):
    """When all the objects are queried without token, only public data are returned.
    If the token is used, the data for the corresponding projects are returned along with the public data."""
    resp = client.get(endpoint)
    assert resp.status_code == 200
    assert resp.content_type == 'application/json'
    results = json.loads(resp.get_data())
    assert set([i['project_id'] for i in results]) == {None}
    for token, projects in tokens.items():
        resp = client.get(endpoint, headers={'Authorization': 'Bearer {}'.format(token)})
        assert resp.status_code == 200
        results = json.loads(resp.get_data())
        assert set([i['project_id'] for i in results]) <= set(projects + [None])


@mark.parametrize('endpoint', ENDPOINTS)
def test_get_one(client, tokens, endpoint):
    """When one object is queried with or without token return it only if it has the allowed project ID.
    Otherwise return 404 Not found."""
    public_data = json.loads(client.get(endpoint).get_data())
    public_object = public_data[0]
    resp = client.get(endpoint + '/{}'.format(public_object['id']))
    assert resp.status_code == 200
    for token, projects in tokens.items():
        headers = {'Authorization': 'Bearer {}'.format(token)}
        resp = client.get(endpoint + '/{}'.format(public_object['id']), headers=headers)
        assert resp.status_code == 200
        result = json.loads(resp.get_data())
        assert public_object == result
        private_data = json.loads(client.get(endpoint, headers=headers).get_data())
        private_object = [d for d in private_data if d['project_id'] is not None][0]
        resp = client.get(endpoint + '/{}'.format(private_object['id']), headers=headers)
        assert resp.status_code == 200
        result = json.loads(resp.get_data())
        assert private_object == result
        resp = client.get(endpoint + '/{}'.format(private_object['id']))
        assert resp.status_code == 404


@mark.parametrize('pair', POST_SIMPLE)
def test_post_and_delete(client, tokens, pair):
    """POST request can only be made by an authorised user with the valid project id.
    Objects with empty project id cannot be created."""
    endpoint, new_object = pair
    resp = client.post(endpoint, data=json.dumps(new_object), headers={
                'Content-Type': 'application/json'
            })
    assert resp.status_code == 401
    projects1, projects2 = tuple(tokens.values())
    for project_id in projects1 + projects2 + [None]:
        for token, projects in tokens.items():
            headers = {
                'Authorization': 'Bearer {}'.format(token),
                'Content-Type': 'application/json'
            }
            new_object['project_id'] = project_id
            resp = client.post(endpoint, data=json.dumps(new_object), headers=headers)
            new_object.pop('project_id')
            if project_id not in projects or project_id is None:
                assert resp.status_code == 400
            else:
                assert resp.status_code == 200
                result = json.loads(resp.get_data())
                assert {k: v for k, v in result.items() if k not in ['id', 'project_id']} == new_object
                headers.pop('Content-Type')
                count = get_count(client, endpoint, headers)
                resp = client.delete(endpoint + '/{}'.format(result['id']), headers=headers)
                assert resp.status_code == 200
                assert get_count(client, endpoint, headers) + 1 == count


def get_count(client, endpoint, headers):
    return len(json.loads(client.get(endpoint, headers=headers).get_data()))
