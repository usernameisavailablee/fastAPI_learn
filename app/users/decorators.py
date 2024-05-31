from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import osmnx as ox
import networkx as nx

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class Coordinate(BaseModel):
    latitude: float
    longitude: float

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit/")
def submit_form(request: Request, coordinates: str = Form(...)):
    coordinates_list = [Coordinate(**coord) for coord in eval(coordinates)]

    if len(coordinates_list) < 2:
        raise HTTPException(status_code=400, detail="At least two points are required to build a route.")

    # Загружаем граф из первой точки
    G = ox.graph_from_point((coordinates_list[0].latitude, coordinates_list[0].longitude), dist=10000, network_type='drive')

    # В виде матрицы
    print("g:",G)

    # Находим ближайшие узлы для каждой точки
    nodes = [ox.distance.nearest_nodes(G, coord.longitude, coord.latitude) for coord in coordinates_list]
    print("nodes:",nodes)

    # Строим маршрут между точками
    route = []
    for i in range(len(nodes) - 1):
        route_segment = nx.shortest_path(G, nodes[i], nodes[i + 1], weight='length')
        print("rs",route_segment)
        route.extend(route_segment if i == 0 else route_segment[1:])

    # Преобразуем маршрут в координаты
    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

    # Преобразуем координаты в список словарей
    coordinates_dicts = [coord.dict() for coord in coordinates_list]

    return templates.TemplateResponse("result.html", {"request": request, "coordinates": coordinates_dicts, "route": route_coords})
