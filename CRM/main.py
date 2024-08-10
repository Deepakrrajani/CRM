from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, Session, declarative_base
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the ORM models
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    inventory_count = Column(Integer, default=0)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    amount = Column(Integer)

    product = relationship("Product")
    customer = relationship("Customer")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

@app.get("/add-product", response_class=HTMLResponse)
async def get_add_product_page(request: Request):
    return templates.TemplateResponse("add_product.html", {"request": request})

@app.post("/add-product")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    inventory_count: int = Form(...),
    db: Session = Depends(get_db)
):
    new_product = Product(name=name, price=price, inventory_count=inventory_count)
    db.add(new_product)
    db.commit()
    return RedirectResponse(url="/products", status_code=302)

@app.get("/products", response_class=HTMLResponse)
async def read_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

@app.get("/update-product/{product_id}", response_class=HTMLResponse)
async def get_update_product_page(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("update_product.html", {"request": request, "product": product})

@app.post("/update-product/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = name
    product.price = price
    db.commit()
    return RedirectResponse(url="/products", status_code=302)

@app.get("/delete-product/{product_id}", response_class=HTMLResponse)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return RedirectResponse(url="/products", status_code=302)

@app.get("/sales", response_class=HTMLResponse)
async def read_sales(request: Request, db: Session = Depends(get_db)):
    sales = db.query(Sale).all()
    total_sales = sum(sale.amount for sale in sales)  # Calculate total sales
    return templates.TemplateResponse("sales.html", {"request": request, "sales": sales, "total_sales": total_sales})


@app.get("/add-sale", response_class=HTMLResponse)
async def get_add_sale_page(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    customers = db.query(Customer).all()
    return templates.TemplateResponse("add_sale.html", {
        "request": request,
        "products": products,
        "customers": customers,
    })

@app.post("/add-sale")
async def add_sale(
    product_name: str = Form(...),
    customer_name: str = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    # Look up the product ID by name
    product = db.query(Product).filter(Product.name == product_name).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Look up the customer ID by name
    customer = db.query(Customer).filter(Customer.name == customer_name).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    new_sale = Sale(product_id=product.id, customer_id=customer.id, amount=amount)
    db.add(new_sale)
    db.commit()
    return RedirectResponse(url="/sales", status_code=302)

@app.get("/customers", response_class=HTMLResponse)
async def read_customers(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return templates.TemplateResponse("customers.html", {"request": request, "customers": customers})

@app.get("/add-customer", response_class=HTMLResponse)
async def get_add_customer_page(request: Request):
    return templates.TemplateResponse("add_customer.html", {"request": request})

@app.post("/add-customer")
async def add_customer(
    name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    new_customer = Customer(name=name, email=email)
    db.add(new_customer)
    db.commit()
    return RedirectResponse(url="/customers", status_code=302)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
