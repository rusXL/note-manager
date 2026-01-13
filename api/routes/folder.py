from fastapi import APIRouter, HTTPException
from models import Folder, SubFolderBase, NoteBase
from database import get_db

router = APIRouter()


@router.get("/folder/{folder_id}", response_model=Folder)
def get_folder(folder_id: int):
    """Get folder name, color, subfolders and notes."""
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            # get the folder
            cur.execute(
                "SELECT id, name, color, description FROM folder WHERE id = %s",
                (folder_id,),
            )
            folder_data = cur.fetchone()

            if not folder_data:
                raise HTTPException(status_code=404, detail="folder not found")

            # get subfolders
            cur.execute(
                "SELECT id, name, color FROM folder WHERE parent_folder_id = %s",
                (folder_id,),
            )  # no need for description
            subfolders = cur.fetchall()

            # get notes
            cur.execute(
                "SELECT id, name FROM note WHERE folder_id = %s", (folder_id,)
            )  # no need for content
            notes = cur.fetchall()

    return Folder(
        **folder_data,
        subfolders=[SubFolderBase(**sf) for sf in subfolders],
        notes=[NoteBase(**n) for n in notes],
    )
