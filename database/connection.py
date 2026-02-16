# database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DB_URL, echo=False)  # echo=True prints SQL queries
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_connection():
    """Return a raw psycopg2 connection to PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "smart_health_hub"),
        user=os.getenv("DB_USER", "openpg"),
        password=os.getenv("DB_PASSWORD", "openpgpwd"),
        port=os.getenv("DB_PORT", "5432")
    )

