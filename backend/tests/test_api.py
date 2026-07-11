from routes import quiz as quiz_routes
from routes import results as results_routes


GOOD_QUESTIONS = [
    {
        "question": f"Q{i}?",
        "options": ["a", "b", "c", "d"],
        "correct_answer": "A",
        "explanation": "e",
    }
    for i in range(5)
]


def _seed_syllabus(mock_db, user_id, topics=("Graphs",)):
    sid = str(mock_db["syllabi"].insert_one(
        {"user_id": user_id, "filename": "s.pdf", "topics": list(topics)}
    ).inserted_id)
    mock_db["plans"].insert_one({
        "syllabus_id": sid,
        "user_id": user_id,
        "sessions": [
            {"topic": t, "date": f"2026-07-{13 + i}", "status": "pending", "description": ""}
            for i, t in enumerate(topics)
        ],
        "version": 1,
    })
    return sid


def test_health_is_public(client):
    assert client.get("/api/health").status_code == 200


def test_quiz_generate_hides_answers(client, mock_db, auth, monkeypatch):
    sid = _seed_syllabus(mock_db, auth["user_id"])
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)

    r = client.post("/api/quiz/generate",
                    json={"syllabus_id": sid, "topic": "Graphs"}, headers=auth["headers"])
    assert r.status_code == 200
    body = r.json()
    assert len(body["questions"]) == 5
    # The correct answer must never leak to the client before submission
    assert all("correct_answer" not in q and "explanation" not in q for q in body["questions"])


def test_quiz_generate_rejects_unknown_syllabus(client, mock_db, auth, monkeypatch):
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    r = client.post("/api/quiz/generate",
                    json={"syllabus_id": "0" * 24, "topic": "Graphs"}, headers=auth["headers"])
    assert r.status_code == 404
    r = client.post("/api/quiz/generate",
                    json={"syllabus_id": "garbage", "topic": "Graphs"}, headers=auth["headers"])
    assert r.status_code == 400


def test_quiz_submit_scores_and_stores_result(client, mock_db, auth, monkeypatch):
    sid = _seed_syllabus(mock_db, auth["user_id"])
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    quiz_id = client.post("/api/quiz/generate",
                          json={"syllabus_id": sid, "topic": "Graphs"},
                          headers=auth["headers"]).json()["quiz_id"]

    r = client.post("/api/quiz/submit",
                    json={"quiz_id": quiz_id, "answers": ["A", "A", "B", "A", "A"]},
                    headers=auth["headers"])
    assert r.status_code == 200
    assert r.json()["score"] == 4
    stored = mock_db["results"].find_one({})
    assert stored["user_id"] == auth["user_id"]


def test_quiz_submit_validates_answers(client, mock_db, auth, monkeypatch):
    sid = _seed_syllabus(mock_db, auth["user_id"])
    monkeypatch.setattr(quiz_routes, "generate_quiz", lambda topic, n=5: GOOD_QUESTIONS)
    quiz_id = client.post("/api/quiz/generate",
                          json={"syllabus_id": sid, "topic": "Graphs"},
                          headers=auth["headers"]).json()["quiz_id"]

    r = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "answers": ["A"]},
                    headers=auth["headers"])
    assert r.status_code == 400
    r = client.post("/api/quiz/submit",
                    json={"quiz_id": quiz_id, "answers": ["A", "A", "X", "A", "A"]},
                    headers=auth["headers"])
    assert r.status_code == 400


def test_results_aggregation_flags_weak_topics(client, mock_db, auth):
    sid = _seed_syllabus(mock_db, auth["user_id"])
    mock_db["results"].insert_many([
        {"syllabus_id": sid, "topic": "Graphs", "score": 2, "total": 5},
        {"syllabus_id": sid, "topic": "Graphs", "score": 3, "total": 5},
        {"syllabus_id": sid, "topic": "Trees", "score": 5, "total": 5},
    ])
    r = client.get(f"/api/results/{sid}", headers=auth["headers"])
    assert r.status_code == 200
    body = r.json()
    assert {t["topic"] for t in body["weak_topics"]} == {"Graphs"}
    assert body["total_quizzes_taken"] == 3


def test_replan_appends_reviews_and_is_idempotent(client, mock_db, auth, monkeypatch):
    sid = _seed_syllabus(mock_db, auth["user_id"])
    mock_db["results"].insert_one({"syllabus_id": sid, "topic": "Graphs", "score": 1, "total": 5})
    fake_reviews = [
        {"topic": "Graphs", "date": "2026-07-14", "status": "pending", "description": "revise", "is_review": True},
        {"topic": "Graphs", "date": "2026-07-15", "status": "pending", "description": "practise", "is_review": True},
    ]
    monkeypatch.setattr(results_routes, "generate_replan", lambda weak, start: fake_reviews)

    r = client.post("/api/replan", json={"syllabus_id": sid}, headers=auth["headers"])
    assert r.status_code == 200
    assert len(r.json()["full_sessions"]) == 3
    assert r.json()["weak_topics_addressed"] == ["Graphs"]

    # Second replan for the same weak topic must refuse, not duplicate
    r2 = client.post("/api/replan", json={"syllabus_id": sid}, headers=auth["headers"])
    assert r2.status_code == 400
    plan = mock_db["plans"].find_one({"syllabus_id": sid})
    assert len(plan["sessions"]) == 3


def test_plan_fetch_restores_state(client, mock_db, auth):
    sid = _seed_syllabus(mock_db, auth["user_id"], topics=("Graphs", "Trees"))
    r = client.get(f"/api/plan/{sid}", headers=auth["headers"])
    assert r.status_code == 200
    body = r.json()
    assert body["topics"] == ["Graphs", "Trees"]
    assert len(body["sessions"]) == 2


def test_mark_session_done_and_undone(client, mock_db, auth):
    sid = _seed_syllabus(mock_db, auth["user_id"], topics=("Graphs", "Trees"))

    r = client.patch(f"/api/plan/{sid}/sessions/1", json={"status": "done"}, headers=auth["headers"])
    assert r.status_code == 200
    assert r.json()["sessions"][1]["status"] == "done"
    assert mock_db["plans"].find_one({"syllabus_id": sid})["sessions"][1]["status"] == "done"

    r = client.patch(f"/api/plan/{sid}/sessions/1", json={"status": "pending"}, headers=auth["headers"])
    assert r.json()["sessions"][1]["status"] == "pending"

    # Out of range / invalid status
    assert client.patch(f"/api/plan/{sid}/sessions/9",
                        json={"status": "done"}, headers=auth["headers"]).status_code == 404
    assert client.patch(f"/api/plan/{sid}/sessions/0",
                        json={"status": "skipped"}, headers=auth["headers"]).status_code == 422


def test_syllabi_dashboard_list(client, mock_db, auth):
    sid = _seed_syllabus(mock_db, auth["user_id"], topics=("Graphs", "Trees"))
    client.patch(f"/api/plan/{sid}/sessions/0", json={"status": "done"}, headers=auth["headers"])

    r = client.get("/api/syllabi", headers=auth["headers"])
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["topics"] == 2
    assert items[0]["sessions"] == 2
    assert items[0]["done_sessions"] == 1
