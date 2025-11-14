import pytest
from app import app
from database_handler import (
    init_database,
    get_users,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            init_database()

        yield client


# Правильные действия


def test_get_users_paginated(client):
    """Тестируем GET /users с пагинацией."""
    response = client.get("/users?page=1&per_page=5")

    assert response.status_code == 200

    assert response.content_type == "application/json"

    json_data = response.get_json()
    assert "meta" in json_data
    assert "data" in json_data
    assert json_data["meta"]["page"] == 1
    assert json_data["meta"]["per_page"] == 5
    assert len(json_data["data"]) == 5


def test_create_user_success(client):
    """Тестируем успешное создание пользователя."""

    new_user_data = {"name": "Тестовый Человек", "email": "test.human@example.com"}

    response = client.post("/user", json=new_user_data)

    assert response.status_code == 201
    assert response.content_type == "application/json"

    json_data = response.get_json()
    assert json_data["name"] == new_user_data["name"]
    assert json_data["email"] == new_user_data["email"]
    assert "id" in json_data


def test_get_single_user(client):
    """Тестируем получение одного пользователя по ID."""
    response = client.get("/user/1")
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data["id"] == 1
    assert json_data["name"] == "Елена Смирнова"


# Неправильные действия


def test_get_nonexistent_user(client):
    """Тестируем запрос пользователя с несуществующим ID."""
    response = client.get("/user/99999")
    assert response.status_code == 404
    json_data = response.get_json()
    assert "error" in json_data
    assert json_data["error"] == "User not found"


def test_create_user_duplicate_email(client):
    """Тестируем создание пользователя с уже существующим email."""

    duplicate_user_data = {"name": "Еще Один", "email": "elena.smirnova@example.com"}
    response = client.post("/user", json=duplicate_user_data)

    assert response.status_code == 409
    json_data = response.get_json()
    assert "error" in json_data
    assert "already in use" in json_data["error"]


def test_create_user_missing_fields(client):
    """Тестируем создание пользователя без обязательного поля 'name'."""
    incomplete_data = {"email": "no.name@example.com"}
    response = client.post("/user", json=incomplete_data)

    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert "Missing required fields" in json_data["error"]
