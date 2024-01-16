from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Union

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/submit/")
def submit_form(request: Request, item: str = Form(...)):
    return templates.TemplateResponse("result.html", {"request": request, "item": item})
