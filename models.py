from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(String, ForeignKey('categories.id'), nullable=True)

    subcategories = relationship("Category", backref='parent', remote_side=[id])
    products = relationship("Product", secondary="product_categories", back_populates="categories")

class Product(Base):
    __tablename__ = "products"

    code = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

    categories = relationship("Category", secondary="product_categories", back_populates="products")

class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_code = Column(String, ForeignKey('products.code'), primary_key=True)
    category_id = Column(String, ForeignKey('categories.id'), primary_key=True)