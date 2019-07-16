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

import os

import requests

from warehouse.app import app


def test_iam(monkeypatch, client):
    # Patch the app config with the current JWT public key from IAM
    response = requests.get(f"{os.environ['IAM_API']}/keys")
    response.raise_for_status()
    monkeypatch.setitem(app.config, 'JWT_PUBLIC_KEY', response.json()["keys"][0])

    # Authenticate as test user
    response = requests.post(f"{os.environ['IAM_API']}/authenticate/local", data={'email': "test", 'password': "test"})
    response.raise_for_status()
    result = response.json()

    # Request to local endpoints with the given JWT should be accepted
    headers = {'Authorization': f"Bearer {result['jwt']}"}
    response = client.get('/experiments', headers=headers)
    assert response.status_code == 200
