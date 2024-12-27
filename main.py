from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Category, Product
from parser import get_categories, get_products

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Фоновая задача для парсинга
def start_parsing(db: Session):
    get_categories(db)
    categories = db.query(Category).all()
    for category in categories:
        get_products(db, category.id)

@app.post("/parse")
def parse_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(start_parsing, db)
    return {"message": "Фоновый парсинг запущен"}

# Маршруты для продуктов

@app.get("/products")
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}")
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    return product

@app.put("/products/{product_id}")
def update_product(product_id: int, name: str, price: float, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.name = name
        product.price = price
        db.commit()
        db.refresh(product)
        return product
    else:
        return {"error": "Продукт не найден"}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return {"message": "Продукт удален"}
    else:
        return {"error": "Продукт не найден"}

# Маршруты для категорий

@app.get("/categories")
def read_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

@app.get("/categories/{category_id}")
def read_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    return category

@app.put("/categories/{category_id}")
def update_category(category_id: str, name: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        category.name = name
        db.commit()
        db.refresh(category)
        return category
    else:
        return {"error": "Категория не найдена"}

@app.delete("/categories/{category_id}")
def delete_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
        return {"message": "Категория удалена"}
    else:
        return {"error": "Категория не найдена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)