from fastapi.testclient import TestClient

from terminalbench.api.app import app


def test_health_tasks_and_compare():
    client = TestClient(app)
    assert client.get("/health").json()["tasks"] == 60
    listed = client.get("/tasks").json()
    assert listed["count"] == 60
    held = client.get("/tasks", params={"split": "held_out"}).json()
    assert held["count"] == 35
    compare = client.get("/compare").json()
    assert compare["tuned"]["overall"]["n_success"] == 35
    assert compare["baseline"]["held_out"]["n_success"] == 12
    assert compare["tuned"]["held_out"]["n_success"] == 18
    missing = client.get("/tasks/does-not-exist")
    assert missing.status_code == 404
