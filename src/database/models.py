from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base



class Tag(Base):
    __tablename__ = 'tags'

    name = Column(String, primary_key=True, unique=True, index=True)
    files = relationship('File', secondary='file_tags', back_populates='tags')


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    direction = Column(String, unique=True, index=True)

    tags = relationship('Tag', secondary='file_tags', back_populates='files')


class FileTags(Base):
    __tablename__ = 'file_tags'

    tag_id = Column(Integer, ForeignKey('tags.name'), primary_key=True)
    files_id = Column(Integer, ForeignKey('files.id'), primary_key=True)

