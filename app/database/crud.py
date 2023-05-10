from sqlalchemy.orm import Session

from . import models, schemas


# Create functions to interact with the database
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
    db_file = models.File(**file.dict())
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_tag_by_name(db: Session, tag_name: str):
    '''
    Get tag by name. And return the Tag object
    '''
    tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
    return tag


def get_files_by_tag_query(db: Session, tag_query: list):
    '''
    Get files by tag query
    '''
    db_files = db.query(models.File).filter(models.File.tags.any(models.Tag.name.in_(tag_query))).all()
    return db_files




# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item