from fastapi import FastAPI
from fastapi import Depends, Query, File, Form
from fastapi import UploadFile
from fastapi.responses import HTMLResponse

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.database import crud, models, schemas, tools
from app.database.database import engine, DatabaseSession
from app.database.schemas import TagCreate, FileCreate


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
def get_db(seccion):
    db = seccion()
    try:
        return db
    finally:
        db.close()

@app.post('/add', summary='Copy the files to the system and assign them the tags')
def add(
        file_list: Annotated[List[UploadFile], File(...)],
        tag_list: Annotated[List[str], Form(...)],
        db: Session = Depends(get_db)
    ):
    files = [FileCreate(file=f, name=f.filename) for f in file_list]
    tags = [TagCreate(name=t) for t in tag_list]
    
    return crud._add(db, files=files, tags=tags)

@app.delete('/delete', summary='Delete all the files that match the tag query')
def delete(
        tag_query: Annotated[List[str], Query()],
        db: Session = Depends(get_db)
    ):
    return crud._delete(db, tag_query=tag_query)

@app.get('/list/', response_model=List[schemas.File], summary='List the name and the tags of every file that match the tag query')
def qlist(
        tag_query: Annotated[List[str], Query()],
        db: Session = Depends(get_db)
    ):
    return crud._list(db, tag_query=tag_query)

@app.post('/add_tags', summary='Add the tags from the tag list to the files that match the tag query')
def add_tags(
        tag_query: List[str],
        tag_list: List[str],
        db: Session = Depends(get_db)
    ):
    return crud._add_tags(db, tag_query=tag_query, tag_list=tag_list)

@app.delete('/delete_tags', summary='Delete the tags from the tag list to the files that match the tag query')
def delete_tags(
        tag_query: Annotated[List[str], Query()],
        tag_list: Annotated[List[str], Query()],
        db: Session = Depends(get_db)
    ):
    return crud._delete_tags(db, tag_query=tag_query, tag_list=tag_list)

@app.get("/")
def main():
    return {'message': 'Hi'}