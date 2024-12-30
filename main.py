import asyncio

from fastapi import FastAPI, Depends, BackgroundTasks, WebSocket, HTTPException
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
async def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@app.get("/products/{product_code}")
async def read_product(product_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
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
        raise HTTPException(status_code=404, detail="Product not found")


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
        return {"message": f"Deleted product with code ${product_code}"}
    else:
        raise HTTPException(status_code=404, detail="Product not found")


@app.get("/categories")
async def read_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories


@app.get("/categories/{category_id}")
async def read_category(category_id: str, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
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
        raise HTTPException(status_code=404, detail="Category not found")


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
        return
    else:
        raise HTTPException(status_code=404, detail="Category not found")


@app.get("/categories/{category_id}/products")
async def read_category_products(category_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        products = db.query(Product).filter(Product.categories.any(id=category_id)).offset(skip).limit(limit).all()
        return products
    else:
        raise HTTPException(status_code=404, detail="Category not found")


@app.get("/products/{product_code}/categories")
def read_product_categories(product_code: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    if product:
        return product.categories
    else:
        raise HTTPException(status_code=404, detail="Product not found")


@app.post("/products/{product_code}/categories/{category_id}")
async def add_product_to_category(product_code: str, category_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    category = db.query(Category).filter(Category.id == category_id).first()
    if product and category:
        if category in product.categories:
            raise HTTPException(status_code=400, detail="Product already in category")
        product.categories.append(category)
        db.commit()
        db.refresh(product)
        await websocket_manager.broadcast({
            "action": "product_added_to_category",
            "product_code": product.code,
            "category_id": category.id
        })
        return {
            "code": product.code,
            "name": product.name,
            "price": product.price,
            "categories": product.categories
        }
    raise HTTPException(status_code=404, detail="Product or category not found")


@app.delete("/products/{product_code}/categories/{category_id}")
async def remove_product_from_category(product_code: str, category_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.code == product_code).first()
    category = db.query(Category).filter(Category.id == category_id).first()
    if product and category:
        if category not in product.categories:
            raise HTTPException(status_code=400, detail="Product not in category")
        product.categories.remove(category)
        db.commit()
        db.refresh(product)
        await websocket_manager.broadcast({
            "action": "product_removed_from_category",
            "product_code": product.code,
            "category_id": category.id
        })
        return {
            "code": product.code,
            "name": product.name,
            "price": product.price,
            "categories": product.categories
        }
    raise HTTPException(status_code=404, detail="Product or category not found")


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
