from pydantic import BaseModel
from typing import Union


# Base classes
class TagBase(BaseModel):
    name: str

class FileBase(BaseModel):
    name: str


# Create classes
class TagCreate(TagBase):
    pass

class FileCreate(FileBase):
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

    class Config:
        orm_mode = True