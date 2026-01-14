from fastapi import APIRouter, HTTPException
from typing import Optional
from models import Folder, FolderBase, NoteBase, Priority

from database import get_db

router = APIRouter()


@router.get("/folder/{folder_id}", response_model=Folder)
def get_folder(
    folder_id: int,
    with_image: bool = False,
    with_caption: bool = False,
    priority: Optional[Priority] = None,
):

    """Get folder name, color, subfolders and notes."""
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            # get the folder
            cur.execute(
                "SELECT id, name, color, description, parent_folder_id FROM folder WHERE id = %s",
                (folder_id,),
            )
            folder_data = cur.fetchone()

            if not folder_data:
                raise HTTPException(status_code=404, detail="folder not found")

            # get subfolders
            cur.execute(
                "SELECT id, name, color, parent_folder_id FROM folder WHERE parent_folder_id = %s",
                (folder_id,),
            )  # no need for description
            subfolders = cur.fetchall()

            # get notes
            query = "SELECT n.id, n.name FROM note n"
            params = [folder_id]
            joins = []
            conditions = ["n.folder_id = %s"]

            if with_image or with_caption:
                joins.append("JOIN image i ON n.id = i.note_id")
                if with_caption:
                    conditions.append("i.caption IS NOT NULL")

            if priority is not None:
                joins.append("JOIN task_note t ON n.id = t.note_id")
                conditions.append("t.priority = %s")
                params.append(priority.value)

            full_query = f"{query} {' '.join(joins)} WHERE {' AND '.join(conditions)}"

            cur.execute(full_query, tuple(params))
            notes = cur.fetchall()


    return Folder(
        **folder_data,
        subfolders=[FolderBase(**sf) for sf in subfolders],
        notes=[NoteBase(**n) for n in notes],
    )
