from os import makedirs
from sqlalchemy.orm import Session

from . import models, schemas, tools




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


