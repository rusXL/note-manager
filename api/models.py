from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    high = 0
    mid = 1
    low = 2


# Base models
class FolderBase(BaseModel):
    id: Optional[str] = None
    name: str
    color: str
    parent_folder_id: Optional[str] = None  # if present makes it a subfolder


class NoteBase(BaseModel):
    id: Optional[str] = None  # None for note add
    name: str


class ImageBase(BaseModel):
    note_id: Optional[str] = None  # None for image add
    url: str
    caption: Optional[str] = None


# Full models
class Folder(FolderBase):
    description: Optional[str] = None
    subfolders: List[FolderBase] = []
    notes: List[NoteBase] = []


class Note(NoteBase):
    folder_id: str
    content: str
    # TaskNote
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    # Image
    image: Optional[ImageBase] = None
