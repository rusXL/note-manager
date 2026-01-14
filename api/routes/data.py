from fastapi import APIRouter, HTTPException
from database import get_db, init_db, is_sql_mode
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

    if is_sql_mode():
        return _init_sql_data(fake)
    else:
        return _init_mongo_data(fake)


def _init_sql_data(fake: Faker):
    """Initialize SQL database with mock data."""
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
            folder_id=str(root_folder_id),
        )
    )

    # 2. create a note with an image but no caption (no caption)
    add_note(
        Note(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=str(root_folder_id),
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
            folder_id=str(root_folder_id),
            priority=Priority.low,
            deadline=date.today(),
        )
    )

    return {
        "root": "folder/1",
    }


def _init_mongo_data(fake: Faker):
    """Initialize MongoDB database with mock data."""
    from bson import ObjectId

    with get_db() as db:
        # Create user
        user_doc = {
            "email": USERS[0]["email"],
            "password": hash_password(USERS[0]["password"]),
            "name": USERS[0]["name"],
            "folders": [],  # will update after creating folders
        }
        user_result = db.users.insert_one(user_doc)
        user_id = user_result.inserted_id

        # Create root folder
        root_folder_doc = {
            "name": "Root",
            "color": "#3498db",
            "description": "Root Folder",
            "user_id": user_id,
            "notes": [],  # will update after creating notes
            "folders": [],  # will update after creating subfolder
        }
        root_result = db.folders.insert_one(root_folder_doc)
        root_folder_id = root_result.inserted_id

        # Create default subfolder inside root
        subfolder_doc = {
            "name": "All Notes",
            "color": "#9b59b6",
            "description": "Default folder for all notes",
            "user_id": user_id,
            "parent_folder_id": root_folder_id,
            "notes": [],
            "folders": [],
        }
        subfolder_result = db.folders.insert_one(subfolder_doc)
        subfolder_id = subfolder_result.inserted_id

        # Update root folder with subfolder reference
        db.folders.update_one(
            {"_id": root_folder_id},
            {"$push": {"folders": {"_id": subfolder_id, "name": "All Notes", "color": "#9b59b6"}}},
        )

        # Update user with folder reference
        db.users.update_one(
            {"_id": user_id},
            {"$push": {"folders": {"_id": root_folder_id, "name": "Root", "color": "#3498db"}}},
        )

        # Note 1: plain note without image
        note1_name = fake.sentence(nb_words=4)
        note1_doc = {
            "parent_folder": root_folder_id,
            "name": note1_name,
            "content": fake.text(),
        }
        note1_result = db.notes.insert_one(note1_doc)
        note1_id = note1_result.inserted_id

        # Note 2: note with image (no caption)
        note2_name = fake.sentence(nb_words=4)
        note2_doc = {
            "parent_folder": root_folder_id,
            "name": note2_name,
            "content": fake.text(),
            "image": {
                "url": f"https://picsum.photos/seed/{random.randint(1, 1000)}/800/600",
                "caption": None,
            },
        }
        note2_result = db.notes.insert_one(note2_doc)
        note2_id = note2_result.inserted_id

        # Note 3: task note with priority and deadline
        note3_name = fake.sentence(nb_words=4)
        note3_doc = {
            "parent_folder": root_folder_id,
            "name": note3_name,
            "content": fake.text(),
            "deadline": str(date.today()),
            "priority": Priority.low.value,
        }
        note3_result = db.notes.insert_one(note3_doc)
        note3_id = note3_result.inserted_id

        # Update root folder with note references
        db.folders.update_one(
            {"_id": root_folder_id},
            {
                "$push": {
                    "notes": {
                        "$each": [
                            {"_id": note1_id, "name": note1_name},
                            {"_id": note2_id, "name": note2_name},
                            {"_id": note3_id, "name": note3_name},
                        ]
                    }
                }
            },
        )

    return {
        "root": f"folder/{str(root_folder_id)}",
    }
