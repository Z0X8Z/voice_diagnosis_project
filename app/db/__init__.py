# app/db/__init__.py
from sqlalchemy.ext.declarative import declarative_base
from .session import engine, SessionLocal

Base = declarative_base()
