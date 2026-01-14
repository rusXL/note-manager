from fastapi import APIRouter, HTTPException
from typing import Optional
from models import Folder, FolderBase, NoteBase, Priority

from database import get_db, is_sql_mode

router = APIRouter()


@router.get("/folder/{folder_id}", response_model=Folder)
def get_folder(
    folder_id: str,
    with_image: bool = False,
    with_caption: bool = False,
    priority: Optional[Priority] = None,
):
    """Get folder name, color, subfolders and notes."""
    if is_sql_mode():
        return _get_folder_sql(int(folder_id), with_image, with_caption, priority)
    else:
        return _get_folder_mongo(folder_id, with_image, with_caption, priority)


def _get_folder_sql(
    folder_id: int,
    with_image: bool,
    with_caption: bool,
    priority: Optional[Priority],
) -> Folder:
    """Get folder from SQL database."""
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

            # get notes (with filters)
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
        id=str(folder_data["id"]),
        name=folder_data["name"],
        color=folder_data["color"],
        description=folder_data.get("description"),
        parent_folder_id=(
            str(folder_data["parent_folder_id"])
            if folder_data.get("parent_folder_id")
            else None
        ),
        subfolders=[
            FolderBase(
                id=str(sf["id"]),
                name=sf["name"],
                color=sf["color"],
                parent_folder_id=(
                    str(sf["parent_folder_id"]) if sf.get("parent_folder_id") else None
                ),
            )
            for sf in subfolders
        ],
        notes=[NoteBase(id=str(n["id"]), name=n["name"]) for n in notes],
    )


def _get_folder_mongo(
    folder_id: str,
    with_image: bool,
    with_caption: bool,
    priority: Optional[Priority],
) -> Folder:
    """Get folder from MongoDB database."""
    with get_db() as db:
        folder_doc = db.folders.find_one({"_id": folder_id})

        if not folder_doc:
            raise HTTPException(status_code=404, detail="folder not found")

        # get embedded basic subfolders
        subfolders_data = folder_doc.get("folders", [])
        subfolders = []
        for sf in subfolders_data:
            subfolders.append(
                FolderBase(
                    id=str(sf["_id"]),
                    name=sf["name"],
                    color=sf["color"],
                    parent_folder_id=str(folder_doc["_id"]),
                )
            )

        # Get notes - need to query notes collection with filters
        note_query = {"parent_folder": folder_id}

        # Build pipeline for filtering
        pipeline = [{"$match": note_query}]

        if with_image or with_caption:
            # Filter for notes that have image field
            pipeline.append({"$match": {"image": {"$exists": True, "$ne": None}}})
            if with_caption:
                pipeline.append(
                    {"$match": {"image.caption": {"$exists": True, "$ne": None}}}
                )

        if priority is not None:
            pipeline.append({"$match": {"priority": priority.value}})

        # Project only id and name
        pipeline.append({"$project": {"_id": 1, "name": 1}})

        notes_cursor = db.notes.aggregate(pipeline)
        notes = []
        for n in notes_cursor:
            notes.append(NoteBase(id=str(n["_id"]), name=n["name"]))

        return Folder(
            id=str(folder_doc["_id"]),
            name=folder_doc["name"],
            color=folder_doc["color"],
            description=folder_doc.get("description"),
            parent_folder_id=(
                str(folder_doc["parent_folder_id"])
                if folder_doc.get("parent_folder_id")
                else None
            ),
            subfolders=subfolders,
            notes=notes,
        )
