from flask import Flask, jsonify, request
from flask_cors import CORS
from database_handler import get_user, get_user_by_email, get_users, post_user

import re

app = Flask(__name__)
CORS(app)  # кросс-доменные запросы со всех источников


@app.get("/users")
def users():
    """
    Возвращает пагинированный список всех пользователей.

    Принимает query-параметры `page` и `per_page` для управления пагинацией.
    В случае ошибки на стороне БД возвращает ошибку 500.
    """
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except (TypeError, ValueError):
        page = 1
        per_page = 10

    # Маленькая валидация(Чтобы ограничить)
    if per_page > 100:
        per_page = 100
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 1

    result = get_users(page=page, per_page=per_page)

    if result is None:
        return jsonify({"error": "A database error occurred"}), 500

    users, total_items = result
    # Формула для безопасного расчета количества страниц, работает даже если total_items = 0
    total_pages = (total_items + per_page - 1) // per_page

    return jsonify(
        {
            "meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_items,
            },
            "data": [dict(row) for row in users],
        }
    )


@app.get("/users/<int:id>")
def user_get(id):
    """
    Возвращает пользователя по его ID.

    Если пользователь не найден, возвращает ошибку 404.
    """
    user = get_user(id=id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user)), 200


@app.post("/user")
def user_post():
    """
    Создает нового пользователя на основе JSON-данных из тела запроса.

    Проводит полную валидацию на наличие полей, типы данных, длину имени,
    формат и уникальность email.

    В случае успеха возвращает созданный объект пользователя и статус 201.
    В случае ошибки возвращает JSON с описанием проблемы и статус (400, 409, 500).
    """
    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    data = request.get_json()

    if not data or "name" not in data or "email" not in data:
        return jsonify({"error": "Missing required fields: name and email"}), 400

    name = data["name"]
    email = data["email"]

    if not isinstance(name, str) or not isinstance(email, str):
        return jsonify({"error": "Fields 'name' and 'email' must be strings"}), 400

    if len(name) < 2 or len(name) > 100:
        return jsonify({"error": "Name must be between 2 and 100 characters"}), 400
    if len(email) < 2 or len(email) > 100:
        return jsonify({"error": "Email must be between 2 and 100 characters"}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email format"}), 400

    if get_user_by_email(email=email) is not None:
        return (
            jsonify({"error": "This email address is already in use"}),
            409,
        )

    new_id = post_user(name=name, email=email)

    if new_id is None:
        return jsonify({"error": "Failed to create user due to a conflict"}), 409

    created_user = get_user(id=new_id)

    if created_user is None:
        return (
            jsonify(
                {
                    "error": "User created, but could not be retrieved due to a server error."
                }
            ),
            500,
        )

    return jsonify(dict(created_user)), 201


@app.errorhandler(404)
def page_not_found(error):
    """
    Глобальный обработчик для ошибок 404 (Not Found).

    Обеспечивает возврат ошибки в формате JSON, даже если запрошен
    несуществующий URL, а не стандартную HTML-страницу Flask.
    """
    return jsonify({"error": "This resource was not found!"}), 404
