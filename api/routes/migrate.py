from fastapi import APIRouter
from database import toggle_db_mode, get_db_mode, get_db, is_sql_mode, init_db
from bson import ObjectId

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

    # Step 4: Insert data into new database and get folder ID mapping
    if is_sql_mode():
        folder_id_map = _insert_to_sql(data)
    else:
        folder_id_map = _insert_to_mongo(data)

    # Step 5: Find root folder ID (folder without parent)
    root_folder_id = None
    for folder in data["folders"]:
        if folder["parent_folder_id"] is None:
            root_folder_id = folder_id_map.get(str(folder["id"]))
            break

    return {
        "mode": new_mode,
        "root": f"folder/{root_folder_id}" if root_folder_id else None,
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
                    "parent_folder_id": str(folder["parent_folder_id"])
                    if folder.get("parent_folder_id")
                    else None,
                }
            )

        # Extract notes
        for note in db.notes.find():
            note_data = {
                "id": str(note["_id"]),
                "name": note["name"],
                "content": note["content"],
                "folder_id": str(note["parent_folder"]),
                "deadline": note.get("deadline"),
                "priority": note.get("priority"),
                "image_url": note.get("image", {}).get("url") if note.get("image") else None,
                "image_caption": note.get("image", {}).get("caption")
                if note.get("image")
                else None,
            }
            data["notes"].append(note_data)

    return data


def _insert_to_sql(data):
    """Insert extracted data into SQL database."""
    # Create ID mapping from old string IDs to new SQL integer IDs
    user_id_map = {}
    folder_id_map = {}
    note_id_map = {}

    with get_db() as conn:
        with conn.cursor() as cur:
            # Insert users
            for user in data["users"]:
                cur.execute(
                    "INSERT INTO user (email, password, name) VALUES (%s, %s, %s)",
                    (user["email"], user["password"], user["name"]),
                )
                user_id_map[str(user["id"])] = cur.lastrowid

            # Insert folders (need to handle parent_folder_id ordering)
            # First pass: insert folders without parent
            pending_folders = []
            for folder in data["folders"]:
                if folder["parent_folder_id"] is None:
                    cur.execute(
                        "INSERT INTO folder (name, color, description, user_id, parent_folder_id) VALUES (%s, %s, %s, %s, NULL)",
                        (
                            folder["name"],
                            folder["color"],
                            folder.get("description"),
                            user_id_map.get(str(folder["user_id"]), 1),
                        ),
                    )
                    folder_id_map[str(folder["id"])] = cur.lastrowid
                else:
                    pending_folders.append(folder)

            # Second pass: insert folders with parents (may need multiple passes for deep nesting)
            max_iterations = 10
            while pending_folders and max_iterations > 0:
                still_pending = []
                for folder in pending_folders:
                    parent_id = folder_id_map.get(str(folder["parent_folder_id"]))
                    if parent_id:
                        cur.execute(
                            "INSERT INTO folder (name, color, description, user_id, parent_folder_id) VALUES (%s, %s, %s, %s, %s)",
                            (
                                folder["name"],
                                folder["color"],
                                folder.get("description"),
                                user_id_map.get(str(folder["user_id"]), 1),
                                parent_id,
                            ),
                        )
                        folder_id_map[str(folder["id"])] = cur.lastrowid
                    else:
                        still_pending.append(folder)
                pending_folders = still_pending
                max_iterations -= 1

            # Insert notes
            for note in data["notes"]:
                folder_id = folder_id_map.get(str(note["folder_id"]))
                if not folder_id:
                    continue  # Skip if folder not found

                cur.execute(
                    "INSERT INTO note (name, content, folder_id) VALUES (%s, %s, %s)",
                    (note["name"], note["content"], folder_id),
                )
                new_note_id = cur.lastrowid
                note_id_map[str(note["id"])] = new_note_id

                # Insert task_note if present
                if note.get("deadline") or note.get("priority") is not None:
                    cur.execute(
                        "INSERT INTO task_note (note_id, deadline, priority) VALUES (%s, %s, %s)",
                        (new_note_id, note.get("deadline"), note.get("priority")),
                    )

                # Insert image if present
                if note.get("image_url"):
                    cur.execute(
                        "INSERT INTO image (note_id, url, caption) VALUES (%s, %s, %s)",
                        (new_note_id, note["image_url"], note.get("image_caption")),
                    )

            conn.commit()

    return folder_id_map

def _insert_to_mongo(data):
    """Insert extracted data into MongoDB database."""
    # Create ID mapping from old SQL integer IDs to new MongoDB ObjectIds
    user_id_map = {}
    folder_id_map = {}

    with get_db() as db:
        # Insert users
        for user in data["users"]:
            user_doc = {
                "email": user["email"],
                "password": user["password"],
                "name": user["name"],
                "folders": [],
            }
            result = db.users.insert_one(user_doc)
            user_id_map[str(user["id"])] = result.inserted_id

        # Insert folders (need to handle parent_folder_id ordering)
        # First pass: insert folders without parent
        pending_folders = []
        for folder in data["folders"]:
            if folder["parent_folder_id"] is None:
                folder_doc = {
                    "name": folder["name"],
                    "color": folder["color"],
                    "description": folder.get("description"),
                    "user_id": user_id_map.get(str(folder["user_id"])),
                    "notes": [],
                    "folders": [],
                }
                result = db.folders.insert_one(folder_doc)
                folder_id_map[str(folder["id"])] = result.inserted_id

                # Update user with folder reference
                db.users.update_one(
                    {"_id": user_id_map.get(str(folder["user_id"]))},
                    {
                        "$push": {
                            "folders": {
                                "_id": result.inserted_id,
                                "name": folder["name"],
                                "color": folder["color"],
                            }
                        }
                    },
                )
            else:
                pending_folders.append(folder)

        # Second pass: insert folders with parents
        max_iterations = 10
        while pending_folders and max_iterations > 0:
            still_pending = []
            for folder in pending_folders:
                parent_id = folder_id_map.get(str(folder["parent_folder_id"]))
                if parent_id:
                    folder_doc = {
                        "name": folder["name"],
                        "color": folder["color"],
                        "description": folder.get("description"),
                        "user_id": user_id_map.get(str(folder["user_id"])),
                        "parent_folder_id": parent_id,
                        "notes": [],
                        "folders": [],
                    }
                    result = db.folders.insert_one(folder_doc)
                    folder_id_map[str(folder["id"])] = result.inserted_id

                    # Update parent folder with subfolder reference
                    db.folders.update_one(
                        {"_id": parent_id},
                        {
                            "$push": {
                                "folders": {
                                    "_id": result.inserted_id,
                                    "name": folder["name"],
                                    "color": folder["color"],
                                }
                            }
                        },
                    )
                else:
                    still_pending.append(folder)
            pending_folders = still_pending
            max_iterations -= 1

        # Insert notes
        for note in data["notes"]:
            folder_id = folder_id_map.get(str(note["folder_id"]))
            if not folder_id:
                continue  # Skip if folder not found

            note_doc = {
                "name": note["name"],
                "content": note["content"],
                "parent_folder": folder_id,
            }

            # Add task fields if present
            if note.get("deadline"):
                note_doc["deadline"] = str(note["deadline"])
            if note.get("priority") is not None:
                note_doc["priority"] = note["priority"]

            # Add image if present
            if note.get("image_url"):
                note_doc["image"] = {
                    "url": note["image_url"],
                    "caption": note.get("image_caption"),
                }

            result = db.notes.insert_one(note_doc)

            # Update folder with note reference
            db.folders.update_one(
                {"_id": folder_id},
                {"$push": {"notes": {"_id": result.inserted_id, "name": note["name"]}}},
            )

    return folder_id_map

@router.get("/mode")
def get_mode():
    return {"mode": get_db_mode()}
