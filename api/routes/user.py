from auth import hash_password
from database import get_db, is_sql_mode
from models import CreateUser


def add_user(user_data: CreateUser) -> dict:
    if is_sql_mode():
        return _add_user_sql(user_data)
    else:
        return _add_user_mongo(user_data)


def _add_user_sql(user_data: CreateUser) -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user (email, password, name) VALUES (%s, %s, %s)",
                (user_data.email, hash_password(user_data.password), user_data.name),
            )

            return {"id": str(cur.lastrowid)}


def _add_user_mongo(user_data: CreateUser) -> dict:
    with get_db() as db:
        user_doc = {
            "email": user_data.email,
            "password": hash_password(user_data.password),
            "name": user_data.name,
        }

        result = db.users.insert_one(user_doc)

        return {"id": str(result.inserted_id)}
