import copy

from fastapi.testclient import TestClient
import pytest

from src.app import app, activities


@pytest.fixture(autouse=True)
def preserve_activities():
    """Make a deep copy of the in-memory activities and restore after each test."""
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original)


def test_get_activities():
    client = TestClient(app)
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Check a known activity exists
    assert "Chess Club" in data


def test_signup_new_participant_and_cleanup():
    client = TestClient(app)
    activity_name = "Chess Club"
    test_email = "test_user@example.com"

    # Ensure test email isn't present
    assert test_email not in activities[activity_name]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Verify participant appears
    resp2 = client.get("/activities")
    assert resp2.status_code == 200
    data = resp2.json()
    assert test_email in data[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    client = TestClient(app)
    activity_name = "Programming Class"
    test_email = "duplicate@example.com"

    # Clean start: ensure not present
    if test_email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(test_email)

    # First signup should succeed
    r1 = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert r1.status_code == 200

    # Second signup should fail with 400
    r2 = client.post(f"/activities/{activity_name}/signup", params={"email": test_email})
    assert r2.status_code == 400
    j = r2.json()
    assert "already" in j.get("detail", "").lower()
