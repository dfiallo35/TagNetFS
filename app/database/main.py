from fastapi import FastAPI
from fastapi import Depends, Query, File, Form
from fastapi import UploadFile
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session
from typing import List, Annotated

from . import crud, models, schemas, tools
from .database import SessionLocal, engine, DatabaseSession
from .schemas import TagCreate, FileCreate


models.Base.metadata.create_all(bind=engine)
app = FastAPI()



# TODO: Caching with Redis
# TODO: Save files
# TODO: Distributed direction of the files in db 

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
@app.post('/add', summary='Copy the files to the system and assign them the tags')
async def add(
        file_list: Annotated[List[UploadFile], File(...)],
        tag_list: Annotated[List[str], Form(...)],
        db: Session = Depends(get_db)
    ):
    
    for file in [FileCreate(file=f, name=f.filename) for f in file_list]:
        db_file = crud.create_file(db, file=file)
        for tag in [TagCreate(name=t) for t in tag_list]:
            db_tag = crud.get_tag_by_name(db, tag.name)
            if db_tag:
                db_file.tags.append(db_tag)
            else:
                db_tag = crud.create_tag(db, tag=tag)
                db_file.tags.append(db_tag)
    db.commit()

    return {"message": "success"}



@app.delete('/delete', summary='Delete all the files that match the tag query')
async def delete(tag_query: Annotated[List[str], Query()], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        db.delete(db_file)
    db.commit()
    return {"message": "success"}



@app.get('/list/', response_model=List[schemas.File], summary='List the name and the tags of every file that match the tag query')
async def qlist(tag_query: Annotated[List[str], Query()], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    return db_files



@app.post('/add_tags', summary='Add the tags from the tag list to the files that match the tag query')
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
    return {"message": "success"}



@app.delete('/delete_tags', summary='Delete the tags from the tag list to the files that match the tag query')
async def delete_tags(tag_query: Annotated[List[str], Query()], tag_list: Annotated[List[str], Query()], db: Session = Depends(get_db)):
    db_files = crud.get_files_by_tag_query(db, tag_query)
    for db_file in db_files:
        for tag in tag_list:
            db_tag = crud.get_tag_by_name(db, tag)
            if db_tag:
                db_file.tags.remove(db_tag)
    db.commit()
    return {"message": "success"}




@app.get("/")
async def main():
    return {'message': 'Hi'}