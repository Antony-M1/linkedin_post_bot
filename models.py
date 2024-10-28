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
    is_posted_personal = Column(Boolean, default=0)
    is_posted_business = Column(Boolean, default=0)
    is_personal = Column(Boolean, default=0)
    is_business = Column(Boolean, default=0)
    is_rejected = Column(Boolean, default=0)
    reason = Column(Text, nullable=True)


def create_engine_session():
    engine = create_engine(f"sqlite:///{os.getenv('DATABASE_NAME')}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session
