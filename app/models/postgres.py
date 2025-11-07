# app/models/postgres.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()


class Code(Base):
    __tablename__ = 'codes'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    url = Column(String, unique=True)
    status = Column(String, default='pending')  # pending, done, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    names = relationship("Name", back_populates="code_obj")


class Name(Base):
    __tablename__ = 'names'

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, ForeignKey('codes.code'))
    name = Column(String, unique=True, index=True)
    url = Column(String, unique=True)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    code_obj = relationship("Code", back_populates="names")
    rawdata = relationship("Rawdata", back_populates="name_obj")
    images = relationship("Image", back_populates="name_obj")


class Rawdata(Base):
    __tablename__ = 'rawdata'

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, ForeignKey('names.name'))
    body_html = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    name_obj = relationship("Name", back_populates="rawdata")


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, ForeignKey('names.name'))
    file_id = Column(String)  # ID файла в MongoDB
    file_url = Column(String)  # оригинальная ссылка
    created_at = Column(DateTime, default=datetime.utcnow)

    name_obj = relationship("Name", back_populates="images")


# Session setup
async def init_db(settings):
    engine = create_async_engine(settings.database.postgres.url, echo=settings.database.postgres.echo)
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
