import asyncio

from fastapi import FastAPI, Depends, BackgroundTasks, WebSocket
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Category, Product
from parser import get_categories, get_products
from websocket_manager import WebSocketManager

Base.metadata.create_all(bind=engine)

app = FastAPI()
websocket_manager = WebSocketManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def start_parsing(db: Session):
    get_categories(db)
    categories = db.query(Category).all()
    asyncio.run(websocket_manager.broadcast({
        "action": "categories_received",
        "length": len(categories)
    }))
    for category in categories:
        get_products(db, category.id)
    asyncio.run(websocket_manager.broadcast({
        "action": "parsing_finished"
    }))

@app.post("/parse")
async def parse_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    await websocket_manager.broadcast({
        "action": "parsing_started"
    })
    background_tasks.add_task(start_parsing, db)
    return {"message": "parsing_started"}

# Маршруты для продуктов

@app.get("/products")
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_code}")
def read_product(product_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    return product

@app.put("/products/{product_code}")
async def update_product(product_code: str, name: str, price: float, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    if product:
        product.name = name
        product.price = price
        db.commit()
        db.refresh(product)
        await websocket_manager.broadcast({
            "action": "product_updated",
            "product": {
                "code": product.code,
                "name": product.name,
                "price": product.price
            }
        })
        return product
    else:
        return {"error": "Продукт не найден"}

@app.delete("/products/{product_code}")
async def delete_product(product_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    if product:
        db.delete(product)
        db.commit()
        await websocket_manager.broadcast({
            "action": "product_deleted",
            "product_code": product_code
        })
        return {"message": "Продукт удален"}
    else:
        return {"error": "Продукт не найден"}

@app.get("/categories")
def read_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

@app.get("/categories/{category_id}")
def read_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    return category

@app.put("/categories/{category_id}")
async def update_category(category_id: str, name: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        category.name = name
        db.commit()
        db.refresh(category)
        await websocket_manager.broadcast({
            "action": "category_updated",
            "category": {
                "id": category.id,
                "name": category.name
            }
        })
        return category
    else:
        return {"error": "Категория не найдена"}

@app.delete("/categories/{category_id}")
async def delete_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
        await websocket_manager.broadcast({
            "action": "category_deleted",
            "category_id": category_id
        })
        return {"message": "Категория удалена"}
    else:
        return {"error": "Категория не найдена"}

@app.get("/categories/{category_id}/products")
def read_category_products(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        return category.products
    else:
        return {"error": "Категория не найдена"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive()
            if data.get('type') == 'websocket.disconnect':
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)