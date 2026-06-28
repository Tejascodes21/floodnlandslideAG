from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.core.config import settings

Base = declarative_base()

# Attempt connection to database with SQLite fallback on failure
DATABASE_URL = settings.DATABASE_URL
engine = None

if DATABASE_URL.startswith("postgresql"):
    try:
        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 3})
        # Test connection
        conn = engine.connect()
        conn.close()
        print("Successfully connected to PostgreSQL database cluster.")
    except (OperationalError, Exception) as e:
        print(f"Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
        DATABASE_URL = "sqlite:///./geoshield.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    print("Initialized serverless SQLite local storage.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import schemas inside init to prevent circular references
    from app.db import schemas
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
