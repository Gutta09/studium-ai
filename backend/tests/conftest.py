import os
import sys

import mongomock
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")


@pytest.fixture()
def mock_db(monkeypatch):
    """Replace the module-level Mongo collections with mongomock equivalents."""
    client = mongomock.MongoClient()
    db = client["studium_test"]

    import auth as auth_module
    import db as db_module
    from routes import quiz as quiz_routes
    from routes import results as results_routes
    from routes import syllabus as syllabus_routes

    mocks = {
        "users": db["users"],
        "syllabi": db["syllabi"],
        "plans": db["plans"],
        "quizzes": db["quizzes"],
        "results": db["results"],
    }
    for name, coll in mocks.items():
        monkeypatch.setattr(db_module, name, coll)
    monkeypatch.setattr(auth_module, "users", mocks["users"])
    monkeypatch.setattr(quiz_routes, "quizzes", mocks["quizzes"])
    monkeypatch.setattr(quiz_routes, "results", mocks["results"])
    monkeypatch.setattr(results_routes, "results_col", mocks["results"])
    monkeypatch.setattr(results_routes, "plans", mocks["plans"])
    monkeypatch.setattr(syllabus_routes, "syllabi", mocks["syllabi"])
    monkeypatch.setattr(syllabus_routes, "plans", mocks["plans"])
    return mocks


@pytest.fixture()
def client(mock_db):
    from main import app
    return TestClient(app)


def make_user(client, email="student@example.com", password="hunter2secure"):
    """Register a user and return (headers, user_id)."""
    r = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    user_id = client.get("/api/auth/me", headers=headers).json()["user_id"]
    return headers, user_id


@pytest.fixture()
def auth(client):
    headers, user_id = make_user(client)
    return {"headers": headers, "user_id": user_id}
