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
    items = relationship("Item", back_populates='category')

    # We added this serialize function to be able to send JSON objects in a serializable format
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'date_created': self.date_created
        }

    @property
    def serialize_with_relations(self):
        return {
            'id': self.id,
            'name': self.name,
            'date_created': self.date_created,
            'items': self.serialize_one2many
        }

    @property
    def serialize_one2many(self):
        return [item.serialize_without_relation for item in self.items]


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    date_created = Column(DateTime, default=_get_datetime, nullable=False)
    owner_mail = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship("Category", back_populates="items")

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

    @property
    def serialize_without_relation(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'date_created': self.date_created,
            'owner_email': self.owner_mail
        }


engine = create_engine('sqlite:///catalogapp.db', connect_args={'check_same_thread': False})

Base.metadata.create_all(engine)
