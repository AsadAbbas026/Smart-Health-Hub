# database/create_tables.py
from database.connection import Base, engine
from database import models

def create_tables():
    # This will create all tables that inherit from Base and don't exist yet
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
