
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(String, ForeignKey('categories.id'), nullable=True)

    subcategories = relationship("Category", backref='parent', remote_side=[id])
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    category_id = Column(String, ForeignKey('categories.id'))

    category = relationship("Category", back_populates="products")