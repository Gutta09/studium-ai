from tests.conftest import make_user


def test_register_login_me_roundtrip(client):
    r = client.post("/api/auth/register", json={"email": "a@b.co", "password": "longenough1"})
    assert r.status_code == 200
    assert "token" in r.json()

    r = client.post("/api/auth/login", json={"email": "A@B.CO", "password": "longenough1"})
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "a@b.co"


def test_duplicate_email_is_409(client):
    client.post("/api/auth/register", json={"email": "a@b.co", "password": "longenough1"})
    r = client.post("/api/auth/register", json={"email": "a@b.co", "password": "different1x"})
    assert r.status_code == 409


def test_wrong_password_and_unknown_email_same_message(client):
    client.post("/api/auth/register", json={"email": "a@b.co", "password": "longenough1"})
    wrong = client.post("/api/auth/login", json={"email": "a@b.co", "password": "wrongwrong1"})
    unknown = client.post("/api/auth/login", json={"email": "x@y.co", "password": "wrongwrong1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_short_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "a@b.co", "password": "short"})
    assert r.status_code == 422


def test_invalid_email_rejected(client):
    r = client.post("/api/auth/register", json={"email": "not-an-email", "password": "longenough1"})
    assert r.status_code == 422


def test_protected_routes_require_token(client):
    assert client.get("/api/syllabi").status_code in (401, 403)
    assert client.get("/api/results/abc").status_code in (401, 403)
    assert client.post("/api/replan", json={"syllabus_id": "abc"}).status_code in (401, 403)


def test_garbage_token_is_401(client):
    r = client.get("/api/syllabi", headers={"Authorization": "Bearer nonsense"})
    assert r.status_code == 401


def test_users_cannot_see_each_others_syllabi(client, mock_db):
    headers_a, user_a = make_user(client, "a@b.co")
    headers_b, _ = make_user(client, "b@b.co")

    sid = str(mock_db["syllabi"].insert_one(
        {"user_id": user_a, "filename": "s.pdf", "topics": ["Graphs"]}
    ).inserted_id)
    mock_db["plans"].insert_one({"syllabus_id": sid, "user_id": user_a, "sessions": []})

    assert client.get(f"/api/plan/{sid}", headers=headers_a).status_code == 200
    # Foreign syllabus must look like it doesn't exist
    assert client.get(f"/api/plan/{sid}", headers=headers_b).status_code == 404
    assert client.get(f"/api/results/{sid}", headers=headers_b).status_code == 404
