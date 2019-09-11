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

"""Test calling the API resource endpoints."""

def test_docs(client):
    """Expect the OpenAPI docs to be served at root."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.content_type == "text/html; charset=utf-8"


def test_admin_authorized(monkeypatch, client, app):
    """Test that the flask-admin interface accepts authenticated requests"""
    monkeypatch.setitem(app.config, "BASIC_AUTH_USERNAME", "giraffe")
    monkeypatch.setitem(app.config, "BASIC_AUTH_PASSWORD", "secret")
    resp = client.get(
        "/admin/", headers={"Authorization": "Basic Z2lyYWZmZTpzZWNyZXQ="}
    )
    assert resp.status_code == 200


def test_admin_unauthorized(monkeypatch, client, app):
    """Test that the flask-admin interface accepts authenticated requests"""
    monkeypatch.setitem(app.config, "BASIC_AUTH_USERNAME", "giraffe")
    monkeypatch.setitem(app.config, "BASIC_AUTH_PASSWORD", "secret")
    resp = client.get(
        "/admin/", headers={"Authorization": "Basic Z2lyYWZmZTppbnZhbGlk"}
    )
    assert resp.status_code == 401
