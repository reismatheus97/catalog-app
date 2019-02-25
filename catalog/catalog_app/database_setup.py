import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


def _get_datetime():
    return datetime.datetime.now()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    date_created = Column(DateTime, default=_get_datetime, nullable=False)

    # We added this serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'date_created': self.date_created,
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    date_created = Column(DateTime, default=_get_datetime, nullable=False)
    owner_mail = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship(Category)

    # We added this serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'date_created': self.date_created,
            'category_id': self.category_id,
            'owner_email': self.owner_mail
        }


engine = create_engine('sqlite:///catalogapp.db', connect_args={'check_same_thread': False})

Base.metadata.create_all(engine)
