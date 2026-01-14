from fastapi import APIRouter, HTTPException
from database import get_db, init_db
from auth import hash_password
from faker import Faker
from models import Note, ImageBase, Priority
from .note import add_note
from datetime import date
import random


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
    fake = Faker()
    root_folder_id = None

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

                conn.commit()

    # student 2 - use case pre-condition
    # 1. Create a note without an image
    add_note(
        Note(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=root_folder_id,
        )
    )

    # 2. create a note with an image but no caption (no caption)
    add_note(
        Note(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=root_folder_id,
            image=ImageBase(
                url=f"https://picsum.photos/seed/{random.randint(1, 1000)}/800/600",
                caption=None,
            ),
        )
    )

    # student 1 - use case pre-condition
    # 1. Create a task note with a low priority
    add_note(
        Note(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=root_folder_id,
            priority=Priority.low,
            deadline=date.today(),
        )
    )

    return {
        "root": "folder/1",
    }
