from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construct the SQLALCHEMY_DATABASE_URL dynamically using the retrieved environment variables
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine for the single database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session maker for the single database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get the database session (single session for all tables)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
