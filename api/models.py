from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import Enum


class Priority(str, Enum):
    high = "high"
    mid = "mid"
    low = "low"


# Base models
class FolderBase(BaseModel):
    id: int
    name: str
    color: str


class SubFolderBase(FolderBase):
    parent_folder_id: int


class NoteBase(BaseModel):
    id: Optional[int] = None  # None for note add
    name: str


class ImageBase(BaseModel):
    note_id: Optional[int] = None  # None for image add
    url: str
    caption: Optional[str] = None


# Full models
class Folder(FolderBase):
    description: Optional[str] = None
    subfolders: List[SubFolderBase]
    notes: List[NoteBase]


class SubFolder(Folder, SubFolderBase):
    pass


class Note(NoteBase):
    folder_id: int
    content: str
    # TaskNote
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    # Image
    image: Optional[ImageBase] = None
