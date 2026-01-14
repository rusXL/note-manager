from fastapi import APIRouter, HTTPException
from models import Note, ImageBase
from database import get_db, is_sql_mode
from datetime import date

router = APIRouter()


@router.get("/note/{note_id}", response_model=Note)
def get_note(note_id: str):
    if is_sql_mode():
        return _get_note_sql(int(note_id))
    else:
        return _get_note_mongo(note_id)


def _get_note_sql(note_id: int) -> Note:
    """Get note from SQL database."""
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            # get note with optional task note fields
            cur.execute(
                """
                SELECT n.id, n.name, n.content, n.folder_id, t.deadline, t.priority
                FROM note n
                LEFT JOIN task_note t ON n.id = t.note_id
                WHERE n.id = %s
            """,
                (note_id,),
            )
            note = cur.fetchone()

            if not note:
                cur.close()
                raise HTTPException(status_code=404, detail="Note not found")

            # get image attached
            cur.execute(
                "SELECT note_id, url, caption FROM image WHERE note_id = %s",
                (note_id,),
            )
            image = cur.fetchone()

            return Note(
                id=str(note["id"]),
                name=note["name"],
                content=note["content"],
                folder_id=str(note["folder_id"]),
                deadline=note.get("deadline"),
                priority=note.get("priority"),
                image=(
                    ImageBase(
                        note_id=str(image["note_id"]),
                        url=image["url"],
                        caption=image.get("caption"),
                    )
                    if image
                    else None
                ),
            )


def _get_note_mongo(note_id: str) -> Note:
    """Get note from MongoDB database."""
    with get_db() as db:
        note_doc = db.notes.find_one({"_id": note_id})

        if not note_doc:
            raise HTTPException(status_code=404, detail="Note not found")

        # Parse deadline if present
        deadline = None
        if note_doc.get("deadline"):
            if isinstance(note_doc["deadline"], str):
                deadline = date.fromisoformat(note_doc["deadline"])
            else:
                deadline = note_doc["deadline"]

        # Parse image if present
        image = None
        if note_doc.get("image"):
            image = ImageBase(
                note_id=str(note_doc["_id"]),
                url=note_doc["image"]["url"],
                caption=note_doc["image"].get("caption"),
            )

        return Note(
            id=str(note_doc["_id"]),
            name=note_doc["name"],
            folder_id=str(note_doc["parent_folder"]),
            content=note_doc["content"],
            deadline=deadline,
            priority=note_doc.get("priority"),
            image=image,
        )


@router.post("/note", response_model=Note)
def add_note(note_data: Note):
    """Create a new note with name, content, optional image and task note fields in a folder."""
    if is_sql_mode():
        return _add_note_sql(note_data)
    else:
        return _add_note_mongo(note_data)


def _add_note_sql(note_data: Note) -> Note:
    """Add note to SQL database."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # verify folder exists
            cur.execute("SELECT id FROM folder WHERE id = %s", (note_data.folder_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Folder not found")

            # create the note
            cur.execute(
                "INSERT INTO note (name, content, folder_id) VALUES (%s, %s, %s)",
                (note_data.name, note_data.content, note_data.folder_id),
            )
            note_id = cur.lastrowid

            # if task note fields provided, create task_note entry
            if note_data.deadline is not None or note_data.priority is not None:
                cur.execute(
                    "INSERT INTO task_note (note_id, deadline, priority) VALUES (%s, %s, %s)",
                    (
                        note_id,
                        note_data.deadline,
                        (
                            note_data.priority.value
                            if note_data.priority is not None
                            else None
                        ),
                    ),
                )

            # if image provided, attach it
            if note_data.image:
                cur.execute(
                    "INSERT INTO image (note_id, url, caption) VALUES (%s, %s, %s)",
                    (note_id, note_data.image.url, note_data.image.caption),
                )

            conn.commit()

            return get_note(note_id=str(note_id))


def _add_note_mongo(note_data: Note) -> Note:
    """Add note to MongoDB database."""
    with get_db() as db:
        folder = db.folders.find_one({"_id": note_data.folder_id})
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        # Build note document
        note_doc = {
            "name": note_data.name,
            "content": note_data.content,
            "parent_folder": note_data.folder_id,
        }

        # Add task note fields if provided
        if note_data.deadline is not None:
            note_doc["deadline"] = str(note_data.deadline)
        if note_data.priority is not None:
            note_doc["priority"] = note_data.priority.value

        # Add image if provided
        if note_data.image:
            note_doc["image"] = {
                "url": note_data.image.url,
                "caption": note_data.image.caption,
            }

        # Insert note
        result = db.notes.insert_one(note_doc)
        note_id = result.inserted_id

        # Update folder with note reference
        db.folders.update_one(
            {"_id": note_data.folder_id},
            {"$push": {"notes": {"_id": note_id, "name": note_data.name}}},
        )

        return get_note(note_id=str(note_id))
