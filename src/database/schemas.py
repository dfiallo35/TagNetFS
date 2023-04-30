from pydantic import BaseModel
from typing import Union


class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    name: str

    class Config:
        orm_mode = True


class FileBase(BaseModel):
    direction: str

class FileCreate(FileBase):
    pass

class File(FileBase):
    id: int
    direction: str

    class Config:
        orm_mode = True

