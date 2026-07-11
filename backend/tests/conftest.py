import os
import sys

import mongomock
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("GROQ_API_KEY", "test-key-not-used")


@pytest.fixture()
def mock_db(monkeypatch):
    """Replace the module-level Mongo collections with mongomock equivalents."""
    client = mongomock.MongoClient()
    db = client["studium_test"]

    import db as db_module
    from routes import quiz as quiz_routes
    from routes import results as results_routes
    from routes import syllabus as syllabus_routes

    mocks = {
        "syllabi": db["syllabi"],
        "plans": db["plans"],
        "quizzes": db["quizzes"],
        "results": db["results"],
    }
    for name, coll in mocks.items():
        monkeypatch.setattr(db_module, name, coll)
    monkeypatch.setattr(quiz_routes, "quizzes", mocks["quizzes"])
    monkeypatch.setattr(quiz_routes, "results", mocks["results"])
    monkeypatch.setattr(quiz_routes, "syllabi", mocks["syllabi"])
    monkeypatch.setattr(results_routes, "results_col", mocks["results"])
    monkeypatch.setattr(results_routes, "plans", mocks["plans"])
    monkeypatch.setattr(syllabus_routes, "syllabi", mocks["syllabi"])
    monkeypatch.setattr(syllabus_routes, "plans", mocks["plans"])
    return mocks
