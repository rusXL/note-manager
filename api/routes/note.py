from fastapi import APIRouter, HTTPException
from models import Note, ImageBase
from database import get_db

router = APIRouter()


@router.get("/note/{note_id}", response_model=Note)
def get_note(note_id: int):
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
                **note,
                image=ImageBase(**image) if image else None,
            )


@router.post("/note", response_model=Note)
def add_note(note_data: Note):
    """Create a new note with name, content, optional image and task note fields in a folder."""
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
                    (note_id, note_data.deadline, note_data.priority),
                )

            # if image provided, attach it
            if note_data.image:
                cur.execute(
                    "INSERT INTO image (note_id, url, caption) VALUES (%s, %s, %s)",
                    (note_id, note_data.image.url, note_data.image.caption),
                )

            conn.commit()

            return get_note(note_id=note_id)
