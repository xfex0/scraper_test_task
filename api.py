from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import json
import uvicorn

app = FastAPI(title="McDonald's Menu API")

with open("menu_data.json", "r", encoding="utf-8") as f:
    menu_data = json.load(f)

@app.get("/menu", summary="Отримати всі продукти")
def get_menu():
    return menu_data

@app.get("/menu/{item_id}", summary="Отримати продукт за ID")
def get_menu_item(item_id: int):
    if 0 <= item_id < len(menu_data):
        return menu_data[item_id]
    raise HTTPException(status_code=404, detail="Елемент не знайдено")

@app.get("/menu/search", summary="Пошук по назві продукту")
def search_menu(query: str = Query(..., description="Ключове слово для пошуку")):
    results = [item for item in menu_data if query.lower() in item["name"].lower()]
    if not results:
        raise HTTPException(status_code=404, detail="Нічого не знайдено")
    return results