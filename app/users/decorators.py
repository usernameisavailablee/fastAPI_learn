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

class AntColonyOptimizer:
    def __init__(self, graph: nx.Graph, nodes: List[int], num_ants, num_iterations, alpha=1, beta=5, rho=0.1, q=1):
        self.graph = graph
        self.nodes = nodes
        self.num_nodes = len(nodes)
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q

        self.pheromone = { (i, j): 1.0 for i in nodes for j in nodes if i != j }
        self.best_solution = None
        self.best_distance = np.inf

    def distance(self, node1, node2):
        try:
            return nx.shortest_path_length(self.graph, source=node1, target=node2, weight='length')
        except nx.NetworkXNoPath:
            return float('inf')

    def ant_tour(self):
        tour = [random.choice(self.nodes)]
        while len(tour) < self.num_nodes:
            current_node = tour[-1]
            move_probs = []
            for node in self.nodes:
                if node not in tour:
                    dist = self.distance(current_node, node)
                    if dist != float('inf'):
                        move_prob = (self.pheromone[(current_node, node)] ** self.alpha) * ((1.0 / dist) ** self.beta)
                        move_probs.append((move_prob, node))
            if not move_probs:
                break
            total = sum(prob for prob, _ in move_probs)
            move_probs = [(prob / total, node) for prob, node in move_probs]
            next_node = random.choices([node for _, node in move_probs], weights=[prob for prob, _ in move_probs], k=1)[0]
            tour.append(next_node)
        return tour

    def ant_colony_optimization(self):
        self.best_solution = None

        for _ in range(self.num_iterations):
            all_solutions = []
            for _ in range(self.num_ants):
                tour = self.ant_tour()
                distance = self.calculate_tour_distance(tour)
                all_solutions.append((tour, distance))
                if distance < self.best_distance:
                    self.best_distance = distance
                    self.best_solution = tour

            self.update_pheromone(all_solutions)

    def calculate_tour_distance(self, tour):
        distance = 0
        for i in range(len(tour) - 1):
            distance += self.distance(tour[i], tour[i + 1])
        distance += self.distance(tour[-1], tour[0])  # Return to the start
        return distance

    def update_pheromone(self, solutions):
        for i, j in self.pheromone.keys():
            self.pheromone[(i, j)] *= (1 - self.rho)

        for tour, distance in solutions:
            for i in range(len(tour) - 1):
                self.pheromone[(tour[i], tour[i + 1])] += self.q / distance
            self.pheromone[(tour[-1], tour[0])] += self.q / distance

@app.post("/submit/")
def submit_form(request: Request, coordinates: str = Form(...)):
    coordinates_list = [Coordinate(**coord) for coord in eval(coordinates)]

    if len(coordinates_list) < 2:
        raise HTTPException(status_code=400, detail="At least two points are required to build a route.")

    # Загружаем граф из первой точки
    G = ox.graph_from_point((coordinates_list[0].latitude, coordinates_list[0].longitude), dist=10000, network_type='drive')

    # Находим ближайшие узлы для каждой точки
    nodes = [ox.distance.nearest_nodes(G, coord.longitude, coord.latitude) for coord in coordinates_list]

    # Убедитесь, что первая точка является первым элементом списка узлов
    start_node = ox.distance.nearest_nodes(G, coordinates_list[0].longitude, coordinates_list[0].latitude)
    nodes.insert(0, start_node)

    # Создаем экземпляр класса AntColonyOptimizer
    aco = AntColonyOptimizer(G, nodes=nodes, num_ants=10, num_iterations=100)
    aco.ant_colony_optimization()

    # Получаем оптимизированный маршрут
    optimal_node_path = aco.best_solution

    if optimal_node_path is None:
        raise HTTPException(status_code=500, detail="Failed to find an optimal path")

    # Преобразуем оптимизированный маршрут в список координат с использованием кратчайших путей
    route = []
    for i in range(len(optimal_node_path) - 1):
        route_segment = nx.shortest_path(G, optimal_node_path[i], optimal_node_path[i + 1], weight='length')
        route.extend(route_segment if i == 0 else route_segment[1:])

    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

    # Преобразуем координаты в список словарей
    coordinates_dicts = [coord.dict() for coord in coordinates_list]

    return templates.TemplateResponse("result.html", {"request": request, "coordinates": coordinates_dicts, "route": route_coords})
