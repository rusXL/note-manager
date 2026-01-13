from fastapi import APIRouter, HTTPException
from database import get_db, init_db
from auth import hash_password

router = APIRouter()

# sample seed data
# a) user with their default (root) folder
USERS = [
    {"email": "alice@example.com", "password": "password", "name": "Alice"},
]


@router.post("/init")
def init():
    """Initialize tables and load hardcoded data (users + default folders)."""
    init_db()

    with get_db() as conn:
        with conn.cursor() as cur:
            # insert users
            for index, user in enumerate(USERS):
                # create user
                cur.execute(
                    "INSERT INTO user (email, password, name) VALUES (%s, %s, %s)",
                    (user["email"], hash_password(user["password"]), user["name"]),
                )

                # create root folder
                cur.execute(
                    "INSERT INTO folder (name, color, description, user_id, parent_folder_id) VALUES (%s, %s, %s, %s, NULL)",
                    (
                        "Root",
                        "#3498db",
                        "Root Folder",
                        index + 1,
                    ),
                )
                root_folder_id = cur.lastrowid

                # create default subfolder inside root
                cur.execute(
                    "INSERT INTO folder (name, color, description, user_id, parent_folder_id) VALUES (%s, %s, %s, %s, %s)",
                    (
                        "All Notes",
                        "#9b59b6",
                        "Default folder for all notes",
                        index + 1,
                        root_folder_id,
                    ),
                )

            conn.commit()  # commit as one transaction

    return {
        "root": "folder/1",
    }
