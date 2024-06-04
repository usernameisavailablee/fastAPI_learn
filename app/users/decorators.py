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
import numpy as np

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class Coordinate(BaseModel):
    latitude: float
    longitude: float

class AntColonyOptimizer:
    def __init__(self, num_cities, num_ants, num_iterations, alpha=1, beta=5, rho=0.1, q=1):
        self.num_cities = num_cities
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q

        self.distances = None
        self.pheromone = None
        self.cities = np.zeros((num_cities, 2))
        self.best_solution = None
        self.best_distance = np.inf

    def generate_cities(self, list_city):
        self.cities = list_city

    def calculate_distances(self):
        self.distances = np.zeros((self.num_cities, self.num_cities))
        for i in range(self.num_cities):
            for j in range(i + 1, self.num_cities):
                distance = np.linalg.norm(self.cities[i] - self.cities[j])
                self.distances[i][j] = distance
                self.distances[j][i] = distance

    def initialize_pheromone(self):
        self.pheromone = np.ones((self.num_cities, self.num_cities))

    def ant_tour(self, ant):
        visited = np.zeros(self.num_cities, dtype=bool)
        tour = np.zeros(self.num_cities, dtype=int)
        current_city = np.random.randint(0, self.num_cities)
        visited[current_city] = True
        tour[0] = current_city

        for _ in range(1, self.num_cities):
            probabilities = np.zeros(self.num_cities)

            for j in range(self.num_cities):
                if not visited[j]:
                    probabilities[j] = (self.pheromone[current_city][j] ** self.alpha) * \
                                       (1.0 / self.distances[current_city][j] ** self.beta)

            probabilities /= np.sum(probabilities)
            next_city = np.random.choice(range(self.num_cities), p=probabilities)
            tour[_] = next_city
            visited[next_city] = True
            current_city = next_city

        return tour

    def ant_colony_optimization(self):
        self.best_solution = np.zeros(self.num_cities, dtype=int)

        for _ in range(self.num_iterations):
            solutions = np.zeros((self.num_ants, self.num_cities), dtype=int)
            distances = np.zeros(self.num_ants)

            for ant in range(self.num_ants):
                solutions[ant] = self.ant_tour(ant)
                distances[ant] = self.calculate_tour_distance(solutions[ant])

                if distances[ant] < self.best_distance:
                    self.best_distance = distances[ant]
                    self.best_solution = np.copy(solutions[ant])

            self.update_pheromone(solutions, distances)

    def calculate_tour_distance(self, tour):
        distance = 0
        for i in range(self.num_cities - 1):
            distance += self.distances[tour[i]][tour[i + 1]]
        distance += self.distances[tour[-1]][tour[0]]  # Add distance from last city to first city
        return distance

    def update_pheromone(self, solutions, distances):
        pheromone_delta = np.zeros((self.num_cities, self.num_cities))

        for ant in range(self.num_ants):
            tour = solutions[ant]
            tour_distance = distances[ant]

            for i in range(self.num_cities - 1):
                pheromone_delta[tour[i]][tour[i + 1]] += self.q / tour_distance

            pheromone_delta[tour[-1]][tour[0]] += self.q / tour_distance

        self.pheromone = (1 - self.rho) * self.pheromone + pheromone_delta

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit/")
def submit_form(request: Request, coordinates: str = Form(...)):
    coordinates_list = [Coordinate(**coord) for coord in eval(coordinates)]

    if len(coordinates_list) < 2:
        raise HTTPException(status_code=400, detail="At least two points are required to build a route.")

    # Prepare cities array for ACO
    cities = np.array([(coord.latitude, coord.longitude) for coord in coordinates_list])
    num_cities = len(cities)

    # Initialize ACO
    aco = AntColonyOptimizer(num_cities=num_cities, num_ants=10, num_iterations=100, alpha=1, beta=5, rho=0.1, q=1)
    aco.generate_cities(cities)
    aco.calculate_distances()
    aco.initialize_pheromone()

    # Run ACO
    aco.ant_colony_optimization()
    best_route = aco.best_solution

    # Get the best route in terms of coordinates
    best_route_coords = [cities[i] for i in best_route]

    # Convert the best route coordinates to a list of dictionaries
    route_coords = [{"latitude": coord[0], "longitude": coord[1]} for coord in best_route_coords]

    # Convert original coordinates to a list of dictionaries
    coordinates_dicts = [coord.dict() for coord in coordinates_list]

    return templates.TemplateResponse("result.html", {"request": request, "coordinates": coordinates_dicts, "route": route_coords})
