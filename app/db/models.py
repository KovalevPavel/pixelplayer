from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    original_name = Column(String, nullable=False)
    minio_object_name = Column(String, unique=True, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="files")
