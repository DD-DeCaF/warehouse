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

import datetime
import itertools
import json
from copy import copy

from pytest import mark


ENDPOINTS = [
    '/strains',
    '/units',
    '/bioentities',
    '/namespaces',
    '/organisms',
    '/types',
    '/media',
    '/experiments',
]


POST_SIMPLE = [
    ('/units', {'name': 'mmol'}),
    ('/namespaces', {'name': 'new namespace'}),
    ('/organisms', {'name': 'mouse'}),
    ('/types', {'name': 'protein'}),
    ('/experiments', {'name': 'new one', 'description': 'the best experiment'}),
    ('/strains', {'name': 'strain', 'genotype': '', 'parent_id': None, 'organism_id': 1}),
    ('/bioentities', {'name': 'reaction1', 'namespace_id': 1, 'reference': '666', 'type_id': 1}),
]


def get_headers(token, no_json=False):
    result = {
        'Authorization': 'Bearer {}'.format(token),
    }
    if no_json:
        return result
    result['Content-Type'] = 'application/json'
    return result


def get_count(client, endpoint, headers):
    return len(json.loads(client.get(endpoint, headers=headers).get_data()))


def test_docs(client):
    """Expect the OpenAPI docs to be served at root."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.content_type == "text/html; charset=utf-8"


@mark.parametrize('endpoint', ENDPOINTS)
def test_get_all(client, db, tokens_read, endpoint):
    """When all the objects are queried without token, only public data are returned.
    If the token is used, the data for the corresponding projects are returned along with the public data."""
    resp = client.get(endpoint)
    assert resp.status_code == 200
    assert resp.content_type == 'application/json'
    results = json.loads(resp.get_data())
    assert set([i['project_id'] for i in results]) == {None}
    for token in tokens_read:
        resp = client.get(endpoint, headers={'Authorization': 'Bearer {}'.format(token['token'])})
        assert resp.status_code == 200
        results = json.loads(resp.get_data())
        assert set([i['project_id'] for i in results]) <= set(token['projects'] + [None])


@mark.parametrize('endpoint', ENDPOINTS)
def test_get_one(client, db, tokens_read, endpoint):
    """When one object is queried with or without token return it only if it has the allowed project ID.
    Otherwise return 404 Not found."""
    public_data = json.loads(client.get(endpoint).get_data())
    public_object = public_data[0]
    resp = client.get(endpoint + '/{}'.format(public_object['id']))
    assert resp.status_code == 200
    for token in tokens_read:
        headers = {'Authorization': 'Bearer {}'.format(token['token'])}
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


@mark.parametrize('endpoint', ENDPOINTS)
def test_crud_public_data(client, db, tokens_write, endpoint):
    """Public data (objects with empty project id) cannot be created."""
    # GET list and single object should be allowed
    response = client.get(f"{endpoint}")
    assert response.status_code == 200
    object_list = response.get_json()
    object_id = object_list[0]['id']
    response = client.get(f"{endpoint}/{object_id}")
    assert response.status_code == 200

    # Use object for put/delete requests
    object_ = response.get_json()

    # Copy object to use as public test object (project_id null)
    new_object = copy(object_)
    del new_object['id']
    new_object['project_id'] = None

    # Write operation are not allowed at all (401 Unauthorized) without token
    response = client.post(f"{endpoint}", data=json.dumps(new_object))
    assert response.status_code == 401
    response = client.put(f"{endpoint}/{object_['id']}", data=json.dumps(object_))
    assert response.status_code == 401
    response = client.delete(f"{endpoint}/{object_['id']}")
    assert response.status_code == 401

    # Write operations are forbidden (403) with valid token
    headers = get_headers(tokens_write[0]['token'])
    # Not allowed to create public data
    response = client.post(f"{endpoint}", data=json.dumps(new_object), headers=headers)
    assert response.status_code == 403
    # Not allowed to modify public data
    response = client.put(f"{endpoint}/{object_['id']}", data=json.dumps(object_), headers=headers)
    assert response.status_code == 403
    response = client.delete(f"{endpoint}/{object_['id']}", headers=headers)
    assert response.status_code == 403


@mark.parametrize('pair', POST_SIMPLE)
def test_post_put_delete(client, db, tokens_admin, pair):
    """POST request can only be made by an authorised user with the valid project id.
    Objects with empty project id cannot be created."""
    endpoint, new_obj = pair
    project_ids = []
    admin_tokens = [t for t in tokens_admin if all([level in ('admin',) for level in t['claims'].values()])]
    for token in admin_tokens:
        project_ids.extend(token['projects'])
    for project_id in project_ids:
        for token in admin_tokens:
            new_object = copy(new_obj)
            headers = get_headers(token['token'])
            new_object['project_id'] = project_id
            resp = client.post(endpoint, data=json.dumps(new_object), headers=headers)
            if project_id not in token['projects']:
                assert resp.status_code == 403
            else:
                assert resp.status_code == 200
                result = json.loads(resp.get_data())
                assert {k: v for k, v in result.items() if k not in ['id', 'created', 'updated']} == new_object
                new_object['name'] = 'PUT'
                resp = client.put(endpoint + '/{}'.format(result['id']), data=json.dumps(new_object), headers=headers)
                assert resp.status_code == 200
                result = json.loads(resp.get_data())
                assert result['name'] == new_object['name']
                content_type = headers.pop('Content-Type')
                count = get_count(client, endpoint, headers)
                resp = client.delete(endpoint + '/{}'.format(result['id']), headers=headers)
                assert resp.status_code == 200
                assert get_count(client, endpoint, headers) + 1 == count
                new_object.pop('name')
                headers['Content-Type'] = content_type
                resp = client.post(endpoint, data=json.dumps(new_object), headers=headers)
                assert resp.status_code == 409


def test_cross_project_strain(client, db, tokens_write):
    """If the modified object is linked to other objects, project IDs should correspond."""
    token1, token2 = tokens_write
    headers = get_headers(token1['token'], no_json=True)
    organisms1 = json.loads(client.get('/organisms', headers=headers).get_data())
    organism_id1 = [o for o in organisms1 if o['project_id'] is not None][0]['id']
    data = {'name': 'strain', 'genotype': '', 'parent_id': None, 'organism_id': organism_id1}
    headers = get_headers(token1['token'])
    resp = client.post('/strains', data=json.dumps(data), headers=headers)
    assert resp.status_code == 403  # nobody can create entities with empty project id
    data['project_id'] = token1['projects'][0]
    resp = client.post('/strains', data=json.dumps(data), headers=headers)
    assert resp.status_code == 200
    data['project_id'] = token2['projects'][0]
    headers = get_headers(token2['token'])
    resp = client.post('/strains', data=json.dumps(data), headers=headers)
    assert resp.status_code == 404  # no access to the project the linked object belongs to


def test_medium(client, db, tokens_admin):
    """Medium endpoints"""
    headers = get_headers(tokens_admin[0]['token'])
    medium_info = {'project_id': tokens_admin[0]['projects'][0], 'name': 'medium1', 'ph': 3}
    compounds_permissions = [1, 2, 5]
    compounds_missing = [1, 666, 3]
    compounds_reactions = [3, 4, 7]
    compounds_correct = [1, 2, 3]

    def get_compounds(ids):
        return [{'id': i, 'mass_concentration': j} for i, j in zip(ids, [0.1, 0.2, 0.3])]

    medium_info['compounds'] = get_compounds(compounds_permissions)
    resp = client.post('/media', data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 404  # no access to the project the linked object belongs to

    medium_info['compounds'] = get_compounds(compounds_missing)
    resp = client.post('/media', data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 404  # no such object

    medium_info['compounds'] = get_compounds(compounds_reactions)
    resp = client.post('/media', data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 404  # not all the linked biological entities are compounds

    medium_info['compounds'] = get_compounds(compounds_correct)
    resp = client.post('/media', data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 200
    medium_id = json.loads(resp.get_data())['id']

    medium_info = {'id': medium_id, 'compounds': get_compounds([1, 2])}
    resp = client.put('/media/{}'.format(medium_id), data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 200
    medium_info = {'id': medium_id, 'compounds': get_compounds([666])}
    resp = client.put('/media/{}'.format(medium_id), data=json.dumps(medium_info), headers=headers)
    assert resp.status_code == 404

    headers.pop('Content-Type')

    resp = client.get('/media/{}'.format(medium_id), headers=headers)
    assert resp.status_code == 200
    assert len(json.loads(resp.get_data())['compounds']) == 2
    resp = client.delete('/media/{}'.format(medium_id), headers=headers)
    assert resp.status_code == 200
    # Check that corresponding compounds are still available
    for compound_id in compounds_correct:
        assert client.get('bioentities/{}'.format(compound_id), headers=headers).status_code == 200


def test_compounds(client):
    resp = client.get('/bioentities/compounds')
    assert resp.status_code == 200
    assert resp.content_type == 'application/json'
    results = json.loads(resp.get_data())
    assert set([i['project_id'] for i in results]) == {None}
    assert set([i['type_id'] for i in results]) == {2}


def test_sample(db, client, tokens_admin):
    """Sample endpoints"""
    headers = get_headers(tokens_admin[0]['token'])
    sample_info = {'name': 'new', 'protocol': 'protocol', 'temperature': 38, 'aerobic': True}
    experiment = {'correct': 1, 'permissions': 3, 'not_existing': 666}
    medium = {'correct': 1, 'permissions': 2, 'not_existing': 666}
    strain = {'correct': 2, 'permissions': 3, 'not_existing': 666}
    for collection in itertools.product(experiment.items(), medium.items(), strain.items()):
        permissions, (experiment_id, medium_id, strain_id) = list(zip(*collection))
        sample_info['medium_id'] = medium_id
        sample_info['strain_id'] = strain_id
        permissions = list(set(permissions))
        resp = client.post('/experiments/{}/samples'.format(experiment_id), data=json.dumps(sample_info),
                           headers=headers)
        if len(permissions) == 1 and permissions[0] == 'correct':
            assert resp.status_code == 200
            new_sample = json.loads(resp.get_data())
        else:
            assert resp.status_code == 404
    for item in itertools.chain(
        zip(experiment.items(), ['experiment_id']*3),
        zip(medium.items(), ['medium_id']*3),
        zip(strain.items(), ['strain_id']*3)
    ):
        (permission, value), key = item
        resp = client.put('/samples/{}'.format(new_sample['id']), data=json.dumps({key: value}), headers=headers)
        if permission == 'correct':
            assert resp.status_code == 200
        else:
            assert resp.status_code == 404
    headers.pop('Content-Type')
    resp = client.get('/experiments/{}/samples'.format(new_sample['experiment_id']), headers=headers)
    assert resp.status_code == 200
    assert len(json.loads(resp.get_data())) > 0
    resp = client.get('/samples/{}'.format(new_sample['id']), headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.get_data()) == new_sample
    resp = client.get('/samples/666', headers=headers)
    assert resp.status_code == 404
    resp = client.delete('/samples/{}'.format(new_sample['id']), headers=headers)
    assert resp.status_code == 200
    resp = client.delete('/samples/666', headers=headers)
    assert resp.status_code == 404


def test_measurements(db, client, tokens_admin):
    """Measurements endpoints"""
    headers = get_headers(tokens_admin[0]['token'])
    measurement_info = {
        'datetime_start': str(datetime.datetime(2018, 1, 1, 12)),
        'datetime_end': str(datetime.datetime(2018, 1, 1, 13)),
        'value': 1,
        'unit_id': 1,
        'numerator_id': 1,
        'denominator_id': None,
    }
    sample = {'correct': 3, 'permissions': 4, 'not_existing': 666}
    for key, value in sample.items():
        resp = client.post('/samples/{}/measurements'.format(value),
                           data=json.dumps([measurement_info]),
                           headers=headers)
        if key == 'correct':
            assert resp.status_code == 200
            obj = json.loads(resp.get_data())[0]
        else:
            assert resp.status_code == 404
    numerator = {'correct': 1, 'permissions': 5, 'not_existing': 666}
    denominator = {'correct': None, 'permissions': 5, 'not_existing': 666}
    for collection in itertools.product(numerator.items(), denominator.items(), sample.items()):
        permissions, (numerator_id, denominator_id, sample_id) = list(zip(*collection))
        permissions = list(set(permissions))
        data = {
            'numerator_id': numerator_id,
            'denominator_id': denominator_id,
            'sample_id': sample_id,
        }
        resp = client.put('/measurements/{}'.format(obj['id']), data=json.dumps(data), headers=headers)
        if len(permissions) == 1 and permissions[0] == 'correct':
            assert resp.status_code == 200
        else:
            assert resp.status_code == 404

    headers.pop('Content-Type')
    resp = client.get('/samples/{}/measurements'.format(sample['correct']), headers=headers)
    assert len(json.loads(resp.get_data())) > 0
    assert resp.status_code == 200

    resp = client.delete('/measurements/{}'.format(obj['id']), headers=headers)
    assert resp.status_code == 200
