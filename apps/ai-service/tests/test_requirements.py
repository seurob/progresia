from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_requirements() -> None:
    response = client.post(
        "/generate-requirements",
        json={
            "name": "Reservas de clases",
            "sector": "Educación",
            "problem": "Gestionar reservas de clases particulares de forma manual",
            "target_users": "Academias y profesores particulares",
            "core_features": ["CRUD de profesores", "Reserva de clases"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_name"] == "Reservas de clases"
    # 2 core features + auth + admin (both default to True)
    assert len(payload["functional_requirements"]) >= 2
