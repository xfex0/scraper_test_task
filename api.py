#api.py

from fastapi import FastAPI, HTTPException
import json
from typing import Optional

app = FastAPI()

# Load data at startup
with open('menu_data.json', 'r', encoding='utf-8') as f:
    menu_data = json.load(f)

@app.get("/all_products/")
def get_all_products():
    return menu_data

@app.get("/products/{product_name}")
def get_product(product_name: str):
    product = next((item for item in menu_data if item['name'].lower() == product_name.lower()), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products/{product_name}/{product_field}")
def get_product_field(product_name: str, product_field: str):
    product = next((item for item in menu_data if item['name'].lower() == product_name.lower()), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product_field not in product:
        raise HTTPException(status_code=404, detail="Field not found")
    
    return {product_field: product[product_field]}