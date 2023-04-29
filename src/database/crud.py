from sqlalchemy.orm import Session

from . import models, schemas



def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tag(db: Session, tag_id: int):
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()

def get_tag_by_name(db: Session, tag_name: int):
    return db.query(models.Tag).filter(models.Tag.name == tag_name).first()


def create_file(db: Session, file: schemas.FileCreate):
    db_file = models.Tag(**file.dict())
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

