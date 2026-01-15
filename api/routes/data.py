from fastapi import APIRouter
from database import init_db
from faker import Faker
from models import CreateNote, Image, Priority, CreateFolder, CreateUser
from auth import hash_password
from .note import add_note
from .folder import add_folder
from .user import add_user
from datetime import date
import random


router = APIRouter()


@router.post("/init")
def init():
    """Initialize the database and load mock data."""
    init_db()

    fake = Faker()

    user_id = add_user(
        CreateUser(name="Alice", email="alice@example.com", password=hash_password("password"))
    )["id"]

    root_folder_id = add_folder(
        CreateFolder(
            name="Root",
            color="#3498db",
            description="Root Folder",
            user_id=user_id,
        )
    )["id"]

    add_folder(
        CreateFolder(
            name="Important Notes",
            color="#9b59b6",
            description="Default folder for important notes",
            user_id=user_id,
            parent_folder_id=root_folder_id,
        )
    )

    # student 2 - use case pre-condition
    # a) create a note without an image
    add_note(
        CreateNote(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=str(root_folder_id),
        )
    )

    # b) create a note with an image but no caption
    add_note(
        CreateNote(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=str(root_folder_id),
            image=Image(
                url=f"https://picsum.photos/seed/{random.randint(1, 1000)}/800/600",
                caption=None,
            ),
        )
    )

    # student 1 - use case pre-condition
    # a) create a task note with a low priority
    add_note(
        CreateNote(
            name=fake.sentence(nb_words=4),
            content=fake.text(),
            folder_id=str(root_folder_id),
            priority=Priority.low,
            deadline=date.today(),
        )
    )

    return {
        "root": f"folder/{root_folder_id}",
    }
