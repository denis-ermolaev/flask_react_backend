import os
import sqlite3
from typing import Tuple

DATABASE = "database.db"


def init_database():
    """
    Удаляет старую БД, создаёт новую, заполняя предустановленными данными
    """
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Старая база данных '{DATABASE}' удалена.")
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        initial_data = [
            ("Елена Смирнова", "elena.smirnova@example.com"),
            ("Дмитрий Кузнецов", "d.kuznetsov@work.net"),
            ("Светлана Попова", "svetlana.p@mail.org"),
            ("Андрей Васильев", "andrey.v@corp.com"),
            ("Ольга Петрова", "olga.petrova1@test.io"),
            ("Виктор Макаров", "v.makarov@domain.net"),
            ("Анастасия Фёдорова", "nastia.f@example.org"),
            ("Игорь Соколов", "igor.sokolov@work.com"),
            ("Юлия Михайлова", "julia.m@test.io"),
            ("Сергей Новиков", "sergey.novikov@corp.net"),
            ("Татьяна Морозова", "t.morozova@example.com"),
            ("Алексей Волков", "alex.volkov@mail.org"),
            ("Марина Лебедева", "marina.lebedeva@work.net"),
            ("Константин Егоров", "k.egorov@domain.com"),
            ("Ирина Козлова", "irina.k@test.io"),
            ("Владимир Павлов", "vlad.pavlov@example.org"),
            ("Екатерина Семёнова", "katya.s@corp.com"),
            ("Роман Захаров", "roman.zakharov@mail.net"),
            ("Дарья Голубева", "dasha.g@work.io"),
            ("Павел Виноградов", "pavel.vinogradov@domain.org"),
        ]
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        """
        )
        cursor.executemany(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            initial_data,
        )
        conn.commit()
        print(f"База данных: '{DATABASE}' создана.")
    finally:
        if conn:
            conn.close()


# Для DRY принципа
def db_func(commit: bool = False):
    """
    Декоратор для сокрытия повторяющегося кода работы с БД,
    благодаря чему можно писать отдельные ф-и с execute и получением данных

    Автоматически открывает и гарантированно закрывает соединение.
    Передает в функции готовый 'cursor' как первый аргумент.

    Если 'commit=True', то после выполнения функции делает conn.commit().
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = None
            try:
                conn = sqlite3.connect(DATABASE)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                result = func(cursor, *args, **kwargs)  #
                if commit:
                    conn.commit()
            finally:
                if conn:
                    conn.close()
            return result

        return wrapper

    return decorator


@db_func()
def get_users(
    cursor: sqlite3.Cursor, page: int = 1, per_page: int = 10
) -> Tuple[list[sqlite3.Row], int] | None:
    """Возвращает срез пользователей для пагинации и общее их количество."""
    cursor.execute("SELECT COUNT(id) FROM users")
    total_items = cursor.fetchone()["COUNT(id)"]

    offset = (page - 1) * per_page

    cursor.execute(
        "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?", (per_page, offset)
    )
    users_on_page = cursor.fetchall()

    return users_on_page, total_items


@db_func()
def get_user(cursor: sqlite3.Cursor, id: int) -> sqlite3.Row | None:
    """Возвращает одного пользователя по его ID."""
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    return cursor.fetchone()


# commit - сохранение изменений БД на диск
@db_func(commit=True)
def post_user(cursor: sqlite3.Cursor, name: str, email: str) -> int | None:
    """Создает нового пользователя и возвращает его ID."""
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    return cursor.lastrowid


@db_func()
def get_user_by_email(cursor: sqlite3.Cursor, email: str) -> sqlite3.Row | None:
    """Находит пользователя по email для проверки уникальности."""
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


if __name__ == "__main__":
    init_database()
