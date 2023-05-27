from pydantic import BaseModel
from typing import List
from fastapi import UploadFile


# Base classes
class TagBase(BaseModel):
    name: str

class FileBase(BaseModel):
    name: str


# Create classes
class TagCreate(TagBase):
    pass

class FileCreate(FileBase):
    file: UploadFile
    pass


# Update classes
class Tag(TagBase):
    id: int
    name: str

    class Config:
        orm_mode = True

class File(FileBase):
    id: int
    name: str
    tags: List[Tag] = []

    class Config:
        orm_mode = True