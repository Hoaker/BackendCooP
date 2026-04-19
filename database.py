import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the URL from the terminal/Render environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Fix for Render's naming convention
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect to Postgres if available, otherwise stay on local SQLite
engine = create_engine(DATABASE_URL or "sqlite:///zimco.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# THESE ARE THE MISSING LINES:
Base = declarative_base()
