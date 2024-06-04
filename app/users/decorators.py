# from fastapi import FastAPI, Request, Form, HTTPException
# from fastapi.templating import Jinja2Templates
# from starlette.staticfiles import StaticFiles
# from pydantic import BaseModel
# from typing import List
# import osmnx as ox
# import networkx as nx
#
# app = FastAPI()
# templates = Jinja2Templates(directory="app/templates")
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
#
# class Coordinate(BaseModel):
#     latitude: float
#     longitude: float
#
# @app.get("/")
# def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})
#
# @app.post("/submit/")
# def submit_form(request: Request, coordinates: str = Form(...)):
#     coordinates_list = [Coordinate(**coord) for coord in eval(coordinates)]
#
#     if len(coordinates_list) < 2:
#         raise HTTPException(status_code=400, detail="At least two points are required to build a route.")
#
#     # Загружаем граф из первой точки
#     G = ox.graph_from_point((coordinates_list[0].latitude, coordinates_list[0].longitude), dist=10000, network_type='drive')
#
#     print("g:",G)
#
#     # Находим ближайшие узлы для каждой точки
#     nodes = [ox.distance.nearest_nodes(G, coord.longitude, coord.latitude) for coord in coordinates_list]
#     print("nodes:",nodes)
#
#     # Строим маршрут между точками
#     route = []
#     for i in range(len(nodes) - 1):
#         route_segment = nx.shortest_path(G, nodes[i], nodes[i + 1], weight='length')
#         print("rs",route_segment)
#         route.extend(route_segment if i == 0 else route_segment[1:])
#
#     # Преобразуем маршрут в координаты
#     route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
#
#     # Преобразуем координаты в список словарей
#     coordinates_dicts = [coord.dict() for coord in coordinates_list]
#
#     return templates.TemplateResponse("result.html", {"request": request, "coordinates": coordinates_dicts, "route": route_coords})
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import osmnx as ox
import networkx as nx
import random
import numpy as np

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class Coordinate(BaseModel):
    latitude: float
    longitude: float

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def ant_colony_optimization(graph: nx.Graph, nodes: List[int], n_ants: int = 10, n_best: int = 5, n_iterations: int = 100, decay: float = 0.5, alpha: float = 1, beta: float = 2) -> List[int]:
    def distance(node1: int, node2: int) -> float:
        try:
            return nx.shortest_path_length(graph, source=node1, target=node2, weight='length')
        except nx.NetworkXNoPath:
            return float('inf')

    pheromone = np.ones((len(nodes), len(nodes)))
    all_time_shortest_path = ("placeholder", np.inf)

    for _ in range(n_iterations):
        all_paths = []
        for _ in range(n_ants):
            path = []
            visited = set()
            start = random.choice(nodes)
            visited.add(start)
            path.append(start)

            prev = start
            for _ in range(len(nodes) - 1):
                move_probs = []
                for node in nodes:
                    if node not in visited:
                        dist = distance(prev, node)
                        if dist == float('inf'):
                            continue
                        move_prob = (pheromone[nodes.index(prev)][nodes.index(node)] ** alpha) * ((1 / dist) ** beta)
                        move_probs.append((move_prob, node))

                if not move_probs:
                    break

                move_probs = sorted(move_probs, key=lambda x: x[0], reverse=True)
                total = sum([prob for prob, node in move_probs])
                probs = [prob / total for prob, node in move_probs]
                next_node = random.choices([node for prob, node in move_probs], weights=probs, k=1)[0]
                path.append(next_node)
                visited.add(next_node)
                prev = next_node

            if len(path) == len(nodes):  # Проверка, что все узлы посещены
                path_distance = sum([distance(path[i], path[i + 1]) for i in range(len(path) - 1)])
                all_paths.append((path, path_distance))

        all_paths = sorted(all_paths, key=lambda x: x[1])
        if all_paths:
            shortest_path = all_paths[0]
            if shortest_path[1] < all_time_shortest_path[1]:
                all_time_shortest_path = shortest_path

        for path, dist in all_paths[:n_best]:
            for move in range(len(path) - 1):
                pheromone[nodes.index(path[move])][nodes.index(path[move + 1])] += 1.0 / dist

        pheromone *= decay

    return all_time_shortest_path[0] if all_time_shortest_path[0] != "placeholder" else nodes

@app.post("/submit/")
def submit_form(request: Request, coordinates: str = Form(...)):
    coordinates_list = [Coordinate(**coord) for coord in eval(coordinates)]

    if len(coordinates_list) < 2:
        raise HTTPException(status_code=400, detail="At least two points are required to build a route.")

    # Загружаем граф из первой точки
    G = ox.graph_from_point((coordinates_list[0].latitude, coordinates_list[0].longitude), dist=10000, network_type='drive')

    # Находим ближайшие узлы для каждой точки
    nodes = [ox.distance.nearest_nodes(G, coord.longitude, coord.latitude) for coord in coordinates_list]

    # Оптимизируем маршрут с помощью муравьиного алгоритма
    optimal_node_path = ant_colony_optimization(G, nodes)

    # Преобразуем оптимизированный маршрут в список координат с использованием кратчайших путей
    route = []
    for i in range(len(optimal_node_path) - 1):
        route_segment = nx.shortest_path(G, optimal_node_path[i], optimal_node_path[i + 1], weight='length')
        route.extend(route_segment if i == 0 else route_segment[1:])

    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

    # Преобразуем координаты в список словарей
    coordinates_dicts = [coord.dict() for coord in coordinates_list]

    return templates.TemplateResponse("result.html", {"request": request, "coordinates": coordinates_dicts, "route": route_coords})
