import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(String(250), primary_key=True)

    @property
    def serialize(self):
        return{
            'id': self.id,
        }


class Quote(Base):
    __tablename__ = 'quote'

    id = Column(Integer, primary_key=True)
    content = Column(String(500), nullable=False)
    author = Column(String(250))
    poster_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(String(250), ForeignKey('category.id'))
    datetime_added = Column(DateTime)
    poster = relationship(User)
    category = relationship(Category)

    @property
    def serialize(self):
        return{
            'content': self.content,
            'author': self.author,
            'poster_id': self.poster_id,
            'category_id': self.category_id,
            'id': self.id
        }


engine = create_engine('postgresql:///quotecamp')
                       #connect_args={'check_same_thread': False})
Base.metadata.create_all(engine)
