from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

Base = declarative_base()
engine = None
SessionLocal = None

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # For local auth
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

def init_db(db_url: str):
    """Initialize the database engine and session."""
    global engine, SessionLocal
    engine = create_engine(db_url, echo=False, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
    #Base.metadata.create_all(bind=engine, checkfirst=True)

def get_db():
    """Provide a transactional scope around a series of operations."""
    global SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
