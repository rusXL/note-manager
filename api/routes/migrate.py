from fastapi import APIRouter
from database import toggle_db_mode, get_db_mode, get_db, is_sql_mode, init_db
from models import CreateUser, CreateFolder, CreateNote, Image
from routes.user import add_user
from routes.folder import add_folder
from routes.note import add_note

router = APIRouter()


@router.post("/migrate")
def migrate():
    """
    Migrate all data from current database to the other database type.
    SQL -> MongoDB or MongoDB -> SQL
    """
    # Step 1: Extract all data from current database
    if is_sql_mode():
        data = _extract_from_sql()
    else:
        data = _extract_from_mongo()

    # Step 2: Toggle database mode
    new_mode = toggle_db_mode()

    # Step 3: Initialize the new database (creates schema/collections)
    init_db()

    # step 4: insert data into new database
    folder_id_map = _insert_data(data)

    # Step 5: Find root folder ID (folder without parent)
    root_folder_id = None
    for folder in data["folders"]:
        if folder["parent_folder_id"] is None:
            root_folder_id = folder_id_map.get(str(folder["id"]))
            break

    return {
        "mode": new_mode,
        "root": f"folder/{str(root_folder_id)}" if root_folder_id else None,
        "migrated": {
            "users": len(data["users"]),
            "folders": len(data["folders"]),
            "notes": len(data["notes"]),
        },
    }


def _extract_from_sql():
    """Extract all data from SQL database."""
    data = {"users": [], "folders": [], "notes": []}

    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            # Extract users
            cur.execute("SELECT id, email, password, name FROM user")
            data["users"] = cur.fetchall()

            # Extract folders
            cur.execute(
                "SELECT id, name, color, description, user_id, parent_folder_id FROM folder"
            )
            data["folders"] = cur.fetchall()

            # Extract notes with task_note and image data
            cur.execute(
                """
                SELECT n.id, n.name, n.content, n.folder_id,
                       t.deadline, t.priority,
                       i.url as image_url, i.caption as image_caption
                FROM note n
                LEFT JOIN task_note t ON n.id = t.note_id
                LEFT JOIN image i ON n.id = i.note_id
                """
            )
            data["notes"] = cur.fetchall()

    return data


def _extract_from_mongo():
    """Extract all data from MongoDB database."""
    data = {"users": [], "folders": [], "notes": []}

    with get_db() as db:
        # Extract users
        for user in db.users.find():
            data["users"].append(
                {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "password": user["password"],
                    "name": user["name"],
                }
            )

        # Extract folders
        for folder in db.folders.find():
            data["folders"].append(
                {
                    "id": str(folder["_id"]),
                    "name": folder["name"],
                    "color": folder["color"],
                    "description": folder.get("description"),
                    "user_id": str(folder["user_id"]),
                    "parent_folder_id": (
                        str(folder["parent_folder_id"])
                        if folder.get("parent_folder_id")
                        else None
                    ),
                }
            )

        # Extract notes
        for note in db.notes.find():
            note_data = {
                "id": str(note["_id"]),
                "name": note["name"],
                "content": note["content"],
                "folder_id": str(note["folder_id"]),
                "deadline": note.get("deadline"),
                "priority": note.get("priority"),
                "image_url": (
                    note.get("image", {}).get("url") if note.get("image") else None
                ),
                "image_caption": (
                    note.get("image", {}).get("caption") if note.get("image") else None
                ),
            }
            data["notes"].append(note_data)

    return data


def _insert_data(data):
    """Insert extracted data into target database using add functions."""
    user_id_map = {}
    folder_id_map = {}

    # insert users (password already hashed from source db)
    for user in data["users"]:
        result = add_user(
            CreateUser(
                email=user["email"],
                password=user["password"],
                name=user["name"],
            )
        )
        user_id_map[str(user["id"])] = result["id"]

    # insert folders without parent first
    pending_folders = []
    for folder in data["folders"]:
        if folder["parent_folder_id"] is None:
            result = add_folder(
                CreateFolder(
                    name=folder["name"],
                    color=folder["color"],
                    description=folder.get("description") or "",
                    user_id=user_id_map.get(str(folder["user_id"]), "1"),
                )
            )
            folder_id_map[str(folder["id"])] = result["id"]
        else:
            pending_folders.append(folder)

    # insert folders with parents (multiple passes for deep nesting)
    max_iterations = 10
    while pending_folders and max_iterations > 0:
        still_pending = []
        for folder in pending_folders:
            parent_id = folder_id_map.get(str(folder["parent_folder_id"]))
            if parent_id:
                result = add_folder(
                    CreateFolder(
                        name=folder["name"],
                        color=folder["color"],
                        description=folder.get("description") or "",
                        user_id=user_id_map.get(str(folder["user_id"]), "1"),
                        parent_folder_id=parent_id,
                    )
                )
                folder_id_map[str(folder["id"])] = result["id"]
            else:
                still_pending.append(folder)
        pending_folders = still_pending
        max_iterations -= 1

    # insert notes
    for note in data["notes"]:
        folder_id = folder_id_map.get(str(note["folder_id"]))
        if not folder_id:
            continue

        image = None
        if note.get("image_url"):
            image = Image(url=note["image_url"], caption=note.get("image_caption"))

        add_note(
            CreateNote(
                name=note["name"],
                content=note["content"],
                folder_id=folder_id,
                deadline=note.get("deadline"),
                priority=note.get("priority"),
                image=image,
            )
        )

    return folder_id_map


@router.get("/mode")
def get_mode():
    return {"mode": get_db_mode()}
