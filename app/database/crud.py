from os import makedirs
import shutil
from sqlalchemy.orm import Session
from os.path import join

from fastapi import Query
from sqlalchemy.orm import Session
from typing import List, Annotated, Tuple

from . import models, schemas, tools
from app.utils.utils import *
from app.database.schemas import TagCreate, FileCreate




def _add(
        db: Session,
        files: List[schemas.FileCreate],
        tags: List[schemas.TagCreate],
):
    for file in files:
        db_file = create_file(db, file=file)
        for tag in tags:
            db_tag = get_tag_by_name(db, tag.name)
            if db_tag:
                db_file.tags.append(db_tag)
            else:
                db_tag = create_tag(db, tag=tag)
                db_file.tags.append(db_tag)
    db.commit()
    return {"message": "success"}

def _delete(
        db: Session,
        tag_query: Annotated[List[str], Query()]
):
    db_files = get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        db.delete(db_file)
    db.commit()
    return {"message": "success"}

def _list(
        db: Session,
        tag_query: Annotated[List[str], Query()],
    ):
    db_files = get_files_by_tag_query(db, tag_query)
    return {file.name:[tag.name for tag in file.tags] for file in db_files}

def _add_tags(
        db: Session,
        tag_query: List[str],
        tag_list: List[str],
    ):
    db_files = get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        for tag in tag_list:
            db_tag = get_tag_by_name(db, tag)
            if db_tag:
                db_file.tags.append(db_tag)
            else:
                db_tag = create_tag(db, tag=schemas.TagCreate(name=tag))
                db_file.tags.append(db_tag)
    db.commit()
    return {"message": "success"}

def _delete_tags(
        db: Session,
        tag_query: Annotated[List[str], Query()],
        tag_list: Annotated[List[str], Query()],
):
    db_files = get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        for tag in tag_list:
            db_tag = get_tag_by_name(db, tag)
            if db_tag:
                db_file.tags.remove(db_tag)
    db.commit()
    return {"message": "success"}


def create_tag(db: Session, tag: schemas.TagCreate):
    '''
    Create tag
    '''
    db_tag = models.Tag(**tag.dict())

    if db.query(models.Tag).filter(models.Tag.name == db_tag.name).first():
        return None
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def create_file(db: Session, file: schemas.FileCreate):
    '''
    Create file
    '''
    makedirs('files', exist_ok=True)
    tools.copy_file(file.file, 'files')
    db_file = models.File(name=file.name)

    exist = db.query(models.File).filter(models.File.name == db_file.name).first()
    if exist:
        return exist
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_tag_by_name(db: Session, tag_name: str):
    '''
    Get tag by name
    '''
    tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
    return tag


def get_files_by_tag_query(db: Session, tag_query: list):
    '''
    Get files by tag query. Tag query is a list of tag names. If file has all tags from tag query, it will be returned. Otherwise, it will not be returned.
    '''
    files = db.query(models.File).all()
    files = [file for file in files if all([tag in [tag.name for tag in file.tags] for tag in tag_query])]
    return files


def get_files_by_name(db: Session, file_name: str):
    '''
    Get file by name.
    '''
    file = db.query(models.File).filter(models.File.name == file_name).first()
    return file


def all_files(db: Session):
    '''
    Get all data from db by file and his tags.
    '''
    files = db.query(models.File).all()
    files = [((tools.get_file(join('files', file.name)), file.name), [_t.name for _t in file.tags]) for file in files]
    return files

def divide_db(db: Session, pieces: int):
    '''
    Divide all the db in n pieces.
    '''
    files = split(all_files(db), pieces)
    return files

def save_files(db: Session, files: List[Tuple[UploadFile, str]]):
    '''
    Save in the db the file list and his tags.
    '''
    for file, tags in files:
        _add(db, [FileCreate(file=tools.dir_to_UploadFile((file[0], file[1])), name=file[1])], [TagCreate(name=t) for t in tags])
    
# FIX
def clear_db(db: Session):
    query = db.query(models.File)
    if list(query):
        for i in list(query):
            db.delete(i)
        db.commit()
    if os.path.exists('files'):
        shutil.rmtree('files')

