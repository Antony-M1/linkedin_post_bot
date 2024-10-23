import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_posted = Column(Integer, default=0)


def create_engine_session():
    engine = create_engine(f"sqlite:///{os.getenv('DATABASE_NAME')}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session