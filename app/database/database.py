from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative

from typing import Any

SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
    echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



import Pyro4
@Pyro4.expose
class DatabaseSession:
    def __init__(self):
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db(self):
        db = self.session()
        try:
            yield db
        finally:
            db.close()



@as_declarative()
class Base:
    id: Any
    __name__: str
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()