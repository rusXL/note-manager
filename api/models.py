from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from enum import IntEnum


class Priority(IntEnum):
    high = 0
    mid = 1
    low = 2


# User
class CreateUser(BaseModel):
    email: str
    password: str
    name: str


# Image
class Image(BaseModel):
    url: str
    caption: Optional[str] = None


# Note
class CreateNote(BaseModel):
    name: str
    folder_id: str
    content: str
    # task note
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    # image
    image: Optional[Image] = None


class NoteBase(BaseModel):
    id: str
    name: str


class NoteWithDetails(NoteBase):
    content: str
    folder_name: str
    user_name: str
    # task note fields
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    # image fields
    image_url: Optional[str] = None
    image_caption: Optional[str] = None


class Note(NoteBase):
    folder_id: str
    content: str
    # task note
    deadline: Optional[date] = None
    priority: Optional[Priority] = None
    # image
    image: Optional[Image] = None


# Folder
class CreateFolder(BaseModel):
    name: str
    color: str
    description: str
    user_id: str
    parent_folder_id: Optional[str] = None


class FolderBase(BaseModel):
    id: str
    name: str
    color: str


class Folder(FolderBase):
    parent_folder_id: Optional[str] = None  # none for root
    description: Optional[str] = None
    subfolders: List[FolderBase] = []
    notes: List[NoteBase] = []
