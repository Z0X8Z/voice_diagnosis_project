# app/db/orm_models.py
from . import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email    = Column(String(100), unique=True, index=True)
    # ……
