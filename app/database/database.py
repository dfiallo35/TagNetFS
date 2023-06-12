from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)


class DatabaseSession:
    def __init__(self):
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_db(self):
        db = self.session()
        try:
            return db
        finally:
            db.close()
