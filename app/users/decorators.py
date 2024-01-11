# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Union
#
# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None
#
#
# app = FastAPI()
#
# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#
# @app.get("/qq")
# def test():
#     return "hello"
#
#
# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.price, "item_id": item_id}

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit/")
def submit_form(request: Request, item: str = Form(...)):
    return templates.TemplateResponse("result.html", {"request": request, "item": item})
