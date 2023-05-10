from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# TODO: Caching with Redis

'''
POST: to create data.
GET: to read data.
PUT: to update data.
DELETE: to delete data.
'''

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# TODO: files names uniques?
# Copy the files to the system and assign them the tags
@app.post('/add', response_model=List[str], summary='Copy the files to the system and assign them the tags')
async def add(file_list: List[schemas.FileCreate], tag_list: List[schemas.TagCreate], db: Session = Depends(get_db)):
    for file in file_list:
        db_file = crud.create_file(db, file=file)
        for tag in tag_list:
            db_tag = crud.get_tag_by_name(db, tag.name)
            if db_tag:
                db_file.tags.append(db_tag)
            else:
                db_tag = crud.create_tag(db, tag=tag)
                db_file.tags.append(db_tag)
    db.commit()

    return [file.name for file in file_list]


# Delete all the files that match the tag query
@app.delete('/delete', summary='Delete all the files that match the tag query')
async def delete(tag_query: List[str], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        db.delete(db_file)
    db.commit()
    return None

# BUG
# List the name and the tags of every file that match the tag query
@app.get('/list', response_model=List[schemas.File], summary='List the name and the tags of every file that match the tag query')
async def list(tag_query: List[str], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    return db_files

# CHECK
# Add the tags from the tag list to the files that match the tag query
@app.post('/add_tags', response_model=None, summary='Add the tags from the tag list to the files that match the tag query')
async def add_tags(tag_query: List[str], tag_list: List[str], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        for tag in tag_list:
            db_tag = crud.get_tag_by_name(db, tag)
            if db_tag:
                db_file.tags.append(db_tag)
            else:
                db_tag = crud.create_tag(db, tag=schemas.TagCreate(name=tag))
                db_file.tags.append(db_tag)
    db.commit()
    return None

# CHECK
# Delete the tags from the tag list to the files that match the tag query
@app.delete('/delete_tags', response_model=None, summary='Delete the tags from the tag list to the files that match the tag query')
async def delete_tags(tag_query: List[str], tag_list: List[str], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        for tag in tag_list:
            db_tag = crud.get_tag_by_name(db, tag)
            if db_tag:
                db_file.tags.remove(db_tag)
    db.commit()
    return None


