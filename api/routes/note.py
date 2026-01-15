from fastapi import APIRouter, HTTPException
from typing import Optional, List
from models import Note, NoteBase, Image, CreateNote, Priority
from database import get_db, is_sql_mode
from bson import ObjectId

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
                "SELECT url, caption FROM image WHERE note_id = %s",
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
                    Image(
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
        note_doc = db.notes.find_one({"_id": ObjectId(note_id)})

        if not note_doc:
            raise HTTPException(status_code=404, detail="Note not found")

        return Note(
            id=str(note_doc["_id"]),
            name=note_doc["name"],
            folder_id=str(note_doc["folder_id"]),
            content=note_doc["content"],
            deadline=note_doc.get("deadline"),
            priority=note_doc.get("priority"),
            image=(
                Image(
                    url=note_doc["image"]["url"],
                    caption=note_doc["image"].get("caption"),
                )
                if note_doc.get("image")
                else None
            ),
        )


@router.get("/notes", response_model=List[NoteBase])
def get_all_notes(
    with_image: bool = False,
    with_caption: bool = False,
    priority: Optional[Priority] = None,
):
    """Get all notes with optional filters."""
    if is_sql_mode():
        return _get_all_notes_sql(with_image, with_caption, priority)
    else:
        return _get_all_notes_mongo(with_image, with_caption, priority)


def _get_all_notes_sql(
    with_image: bool,
    with_caption: bool,
    priority: Optional[Priority],
) -> List[NoteBase]:
    """Get all notes from SQL database with filters."""
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            query = "SELECT DISTINCT n.id, n.name FROM note n"
            joins = []
            conditions = []
            params = []

            if with_image:
                joins.append("JOIN image i ON n.id = i.note_id")

            if with_caption:
                joins.append("JOIN image ic ON n.id = ic.note_id")
                conditions.append("ic.caption IS NOT NULL AND ic.caption != ''")

            if priority is not None:
                joins.append("JOIN task_note t ON n.id = t.note_id")
                conditions.append("t.priority = %s")
                params.append(priority.value)

            if joins:
                query += " " + " ".join(joins)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cur.execute(query, tuple(params))
            notes = cur.fetchall()

            return [NoteBase(id=str(n["id"]), name=n["name"]) for n in notes]


def _get_all_notes_mongo(
    with_image: bool,
    with_caption: bool,
    priority: Optional[Priority],
) -> List[NoteBase]:
    """Get all notes from MongoDB database with filters."""
    with get_db() as db:
        pipeline = []

        if with_image:
            pipeline.append({"$match": {"image": {"$exists": True, "$ne": None}}})

        if with_caption:
            pipeline.append({"$match": {"image.caption": {"$exists": True, "$ne": None, "$ne": ""}}})

        if priority is not None:
            pipeline.append({"$match": {"priority": priority.value}})

        pipeline.append({"$project": {"_id": 1, "name": 1}})

        notes_cursor = db.notes.aggregate(pipeline)
        return [
            NoteBase(id=str(n["_id"]), name=n["name"])
            for n in notes_cursor
        ]


@router.post("/note")
def add_note(note_data: CreateNote) -> dict:
    """Create a new note with name, content, optional image and task note fields in a folder."""
    if is_sql_mode():
        return _add_note_sql(note_data)
    else:
        return _add_note_mongo(note_data)


def _add_note_sql(note_data: CreateNote) -> dict:
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

            return {"id": str(note_id)}


def _add_note_mongo(note_data: CreateNote) -> dict:
    """Add note to MongoDB database."""
    with get_db() as db:
        folder = db.folders.find_one({"_id": ObjectId(note_data.folder_id)})
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

        note_doc = {
            "name": note_data.name,
            "content": note_data.content,
            "folder_id": ObjectId(note_data.folder_id),
        }

        # task note
        if note_data.deadline is not None:
            note_doc["deadline"] = str(note_data.deadline)
        if note_data.priority is not None:
            note_doc["priority"] = note_data.priority.value

        # image
        if note_data.image:
            image_doc = {"url": note_data.image.url}
            if note_data.image.caption:
                image_doc["caption"] = note_data.image.caption
            note_doc["image"] = image_doc

        result = db.notes.insert_one(note_doc)
        note_id = result.inserted_id

        # update folder with note reference
        db.folders.update_one(
            {"_id": ObjectId(note_data.folder_id)},
            {"$push": {"notes": {"_id": note_id, "name": note_data.name}}},
        )

        return {"id": str(note_id)}
