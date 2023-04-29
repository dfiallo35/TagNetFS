from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post('/tag/', response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    db_tag = crud.get_tag_by_name(db, tag.name)
    if db_tag:
        raise HTTPException(status_code=400, detail='Tag alredy exist')
    return crud.create_tag(db, tag=tag)


@app.post('/file/', response_model=schemas.File)
def create_file(file: schemas.FileCreate, db: Session = Depends(get_db)):
    db_file = crud.create_file(db, file=file)
    # TODO: alredy exist


