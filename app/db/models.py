from sqlalchemy import Column, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from .database import Base
from typing import List

class User(Base):
    __tablename__ = "users"
    # id = Column(Integer, primary_key=True, index=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files: Mapped[List["File"]] = relationship("File", back_populates="owner", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_name: Mapped[str] = mapped_column(nullable=False)
    minio_object_name: Mapped[str] = mapped_column(unique=True, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(nullable=False)
    owner_id =  Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner: Mapped["User"] = relationship("User", back_populates="files")
