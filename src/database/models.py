from sqlalchemy import Column, Table, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base, engine



class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    files = relationship('File', secondary='file_tags', back_populates='tags')


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    direction = Column(String, unique=True, index=True)

    tags = relationship('Tag', secondary='file_tags', back_populates='files')


file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('tag_id', ForeignKey('tags.name'), primary_key=True),
    Column('files_id', ForeignKey('files.id'), primary_key=True)
)

Base.metadata.create_all(engine)