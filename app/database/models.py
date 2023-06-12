from typing import Any
from sqlalchemy.orm import relationship, as_declarative
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Table, ForeignKey, Integer, String



@as_declarative()
class Base:
    id: Any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()




class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    files = relationship('File', secondary='file_tags', back_populates='tags')


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    tags = relationship('Tag', secondary='file_tags', back_populates='files')


file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('tag_id', ForeignKey('tags.id'), primary_key=True),
    Column('files_id', ForeignKey('files.id'), primary_key=True)
)
