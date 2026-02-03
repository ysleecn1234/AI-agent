import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "in7user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "in7password")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "in7platform")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# 2. Setup Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Setup Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base Class for Models
Base = declarative_base()

# 5. Dependency for API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
