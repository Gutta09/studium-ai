import pytest
from fastapi.testclient import TestClient

from main import app
from routes import quiz as quiz_routes
from routes import results as results_routes


@pytest.fixture()
def client(mock_db):
    return TestClient(app)


GOOD_QUESTIONS = [
    {
        "question": f"Q{i}?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "A",
        "explanation": "e",
    }
    for i in range(5)
]


def _seed_syllabus(mock_db):
    return str(mock_db["syllabi"].insert_one({"filename": "s.pdf", "topics": ["Graphs"]}).inserted_id)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_quiz_generate_hides_answers(client, mock_db, monkeypatch):
    syllabus_id = _seed_syllabus(mock_db)
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)

    r = client.post("/api/quiz/generate", json={"syllabus_id": syllabus_id, "topic": "Graphs"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["questions"]) == 5
    # The correct answer must never leak to the client before submission
    assert all("correct_answer" not in q and "explanation" not in q for q in body["questions"])


def test_quiz_generate_rejects_unknown_syllabus(client, mock_db, monkeypatch):
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    r = client.post("/api/quiz/generate", json={"syllabus_id": "0" * 24, "topic": "Graphs"})
    assert r.status_code == 404
    r = client.post("/api/quiz/generate", json={"syllabus_id": "garbage", "topic": "Graphs"})
    assert r.status_code == 400


def test_quiz_submit_scores_and_stores_result(client, mock_db, monkeypatch):
    syllabus_id = _seed_syllabus(mock_db)
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    quiz_id = client.post(
        "/api/quiz/generate", json={"syllabus_id": syllabus_id, "topic": "Graphs"}
    ).json()["quiz_id"]

    r = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": ["A", "A", "B", "A", "A"]})
    assert r.status_code == 200
    assert r.json()["score"] == 4
    assert mock_db["results"].count_documents({}) == 1


def test_quiz_submit_validates_answers(client, mock_db, monkeypatch):
    syllabus_id = _seed_syllabus(mock_db)
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    quiz_id = client.post(
        "/api/quiz/generate", json={"syllabus_id": syllabus_id, "topic": "Graphs"}
    ).json()["quiz_id"]

    # Wrong count
    r = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": ["A"]})
    assert r.status_code == 400
    # Invalid letters
    r = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": ["A", "A", "X", "A", "A"]})
    assert r.status_code == 400


def test_results_aggregation_flags_weak_topics(client, mock_db):
    mock_db["results"].insert_many([
        {"syllabus_id": "syl1", "topic": "Graphs", "score": 2, "total": 5},
        {"syllabus_id": "syl1", "topic": "Graphs", "score": 3, "total": 5},
        {"syllabus_id": "syl1", "topic": "Trees", "score": 5, "total": 5},
    ])
    r = client.get("/api/results/syl1")
    assert r.status_code == 200
    body = r.json()
    weak = {t["topic"] for t in body["weak_topics"]}
    assert weak == {"Graphs"}
    assert body["total_quizzes_taken"] == 3


def test_replan_appends_reviews_and_is_idempotent(client, mock_db, monkeypatch):
    mock_db["results"].insert_one({"syllabus_id": "syl1", "topic": "Graphs", "score": 1, "total": 5})
    mock_db["plans"].insert_one({
        "syllabus_id": "syl1",
        "sessions": [{"topic": "Graphs", "date": "2026-07-13", "status": "pending", "description": ""}],
        "version": 1,
    })
    fake_reviews = [
        {"topic": "Graphs", "date": "2026-07-14", "status": "pending", "description": "revise", "is_review": True},
        {"topic": "Graphs", "date": "2026-07-15", "status": "pending", "description": "practise", "is_review": True},
    ]
    monkeypatch.setattr(results_routes, "generate_replan", lambda weak, start: fake_reviews)

    r = client.post("/api/replan", json={"syllabus_id": "syl1"})
    assert r.status_code == 200
    assert len(r.json()["full_sessions"]) == 3
    assert r.json()["weak_topics_addressed"] == ["Graphs"]

    # Second replan for the same weak topic must refuse, not duplicate
    r2 = client.post("/api/replan", json={"syllabus_id": "syl1"})
    assert r2.status_code == 400
    plan = mock_db["plans"].find_one({"syllabus_id": "syl1"})
    assert len(plan["sessions"]) == 3


def test_replan_with_no_weak_topics_is_400(client, mock_db):
    r = client.post("/api/replan", json={"syllabus_id": "nothing"})
    assert r.status_code == 400
