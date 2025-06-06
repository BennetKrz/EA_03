import operator
import random
from tkinter import Tk, Canvas
import neat
import math
import os
os.environ['TCL_LIBRARY'] = r'C:\Users\bjarn\AppData\Local\Programs\Python\Python313\tcl\tcl8.6'

import tkinter as tk
import visualize

# Kantenlänge des Labyrinths
MAP_SIZE = 25
MAX_STEPS = 100

class MapGenerator:
    """
        MapGenerator kümmert sich um die Erzeugung und die Anzeige der
        Labyrinth-Karten.
    """

    def __init__(self, size, start, end):
        self.size = size
        self.start = start
        self.end = end
        self.map = [[0 for _ in range(size)] for _ in range(size)]
        self.tilesize = 20
    
    def generate(self):
        """
           Erzeugt eine Zufallskarte und gibt sie als 2D-Array zurück.
           Eine 0 im Array steht für ein betretbares Feld, 1 für ein
           Hindernis, S für Start und E für Ende.
        """
        
        # Sicherstellen, dass es mindestens einen Pfad vom Start bis zum Ende gibt
        while True:
            #self.map = [[random.randint(0, 1) for _ in range(self.size)] for _ in range(self.size)]
            self.map = [[1 if random.random() < 0.25 else 0 for _ in range(self.size)] for _ in range(self.size)]
            if self._is_valid():
                break

        # Start und Ende Punkte setzen
        self.map[self.start[0]][self.start[1]] = 'S'
        self.map[self.end[0]][self.end[1]] = 'E'

    def _is_valid(self):
        start, end = self.start, self.end
        queue = [start]
        visited = set(queue)
        while queue:
            row, col = queue.pop(0)
            if (row, col) == end:
                return True
            neighbors = self._get_neighbors(row, col)
            for neighbor in neighbors:
                if neighbor not in visited and self.map[neighbor[0]][neighbor[1]] == 0:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def _get_neighbors(self, row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row-1, col))
        if row < self.size-1:
            neighbors.append((row+1, col))
        if col > 0:
            neighbors.append((row, col-1))
        if col < self.size-1:
            neighbors.append((row, col+1))
        return neighbors

    def draw_map(self, agent):
        """
            Erstellt und zeigt die GUI an.
        """

        ts = self.tilesize
        root = Tk()
        root.title('NEAT Maze')
        canvas = Canvas(root, width=self.size*ts, height=self.size*ts)
        canvas.pack()
        for row in range(self.size):
            for col in range(self.size):
                if self.map[col][row] == 'S':
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill='red')
                elif self.map[col][row] == 'E':
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill='blue')
                else:
                    color = 'white' if self.map[col][row] == 0 else 'gray'
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill=color)
        # draw the agent's path
        canvas.create_oval(
                    agent.pos_x*ts+ts*0.25, 
                    agent.pos_y*ts+ts*0.25, 
                    (agent.pos_x+1)*ts-ts*0.25, 
                    (agent.pos_y+1)*ts-ts*0.25, 
                    fill='orange')

        for i in range(0,MAP_SIZE*5):
            inputs = agent._get_map_env()
            output = agent.activate_net(inputs)
            if agent.move(output):
                canvas.create_oval(
                    agent.pos_x*ts+ts*0.25, 
                    agent.pos_y*ts+ts*0.25, 
                    (agent.pos_x+1)*ts-ts*0.25, 
                    (agent.pos_y+1)*ts-ts*0.25, 
                    fill='orange')
                
            if agent.pos_x == 0 and agent.pos_y == 0:
                    break

        root.mainloop()

class Agent:
    """
        Repräsentiert einen Agenten, der sich durch das Labyrinth bewegt.
    """
    
    def __init__(self, net):
        self.net = net
        self.pos_x = None
        self.pos_y = None
        self.goal_x = None
        self.goal_y = None
        self.map = None
        self.visited = set()
        self.fitness = 0.0

    def set_map(self, map):
        self.map = map

    def set_start(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.visited.add((x, y))

    def set_goal(self, x, y):
        self.goal_x = x
        self.goal_y = y

    def activate_net(self, inputs):
        output = self.net.activate(inputs)
        return output.index(max(output))

    def move(self, direction):
        """
            Bewegt den Agenten auf dem Labyrinth. Es muss sichergestellt werden,
            dass der Agent nur zulässige Bewegungen mehr. Die Methode gibt
            True zurück, wenn die Bewegung erfolgreich war, andernfalls False.
        """
        
        def valid_move(x, y):
            if x < 0 or x >= len(self.map) or y < 0 or y >= len(self.map[0]):
                return False
            if (x, y) in self.visited:
                return False
            if self.map[x][y] == 1:
                return False
            if self.map[x][y] == 0 or self.map[x][y] == 'S' or self.map[x][y] == 'E':
                return True
            return False

        if direction == 0:
            delta = (-1, 0)
        elif direction == 1:
            delta = (0, -1)
        elif direction == 2:
            delta = (1, 0)
        else:
            delta = (0, 1)

        if valid_move(self.pos_x+delta[0], self.pos_y+delta[1]):
            self.pos_x += delta[0]
            self.pos_y += delta[1]
            self.visited.add((self.pos_x, self.pos_y))
            return True

        return False

    def _get_distance(self):
        return math.sqrt((self.goal_x - self.pos_x)**2 + (self.goal_y - self.pos_y)**2)

    def _get_map_env(self):
        env = []
        def get_value(x, y):
            if x < 0 or y < 0 or x >= len(self.map) or y >= len(self.map[0]):
                return 1 # value for out-of-bounds indices
            elif self.map[x][y] == 'E' or self.map[x][y] == 'S':
                return 0
            else:
                return self.map[x][y]
        env.append(get_value(self.pos_x - 1, self.pos_y + 1)) # top left
        env.append(get_value(self.pos_x, self.pos_y + 1)) # top middle
        env.append(get_value(self.pos_x + 1, self.pos_y + 1)) # top right
        env.append(get_value(self.pos_x - 1, self.pos_y)) # middle left
        env.append(get_value(self.pos_x + 1, self.pos_y)) # middle right
        env.append(get_value(self.pos_x - 1, self.pos_y - 1)) # bottom left
        env.append(get_value(self.pos_x, self.pos_y - 1)) # bottom middle
        env.append(get_value(self.pos_x + 1, self.pos_y - 1)) # bottom right
        return env


    def run(self):
        """
            Führt eine Maximalanzahl von Schritten für den Agenten aus.
            Die Richtung wird vom "Gehirn", dem neuronalen Netz festgelegt.
        """

        steps = 0
        while steps < MAX_STEPS and not (self.pos_x == self.goal_x and self.pos_y == self.goal_y):

            neighbours = self._get_map_env()
            output = self.net.activate(neighbours)
            next_dirs = [(index, probability) for index, probability in enumerate(output)]
            next_dirs = sorted(next_dirs, key=operator.itemgetter(1), reverse=True)

            for next_dir in next_dirs:
                if self.move(next_dir[0]):
                    break

            steps += 1

        #self.fitness = self._get_distance()
        self.fitness = self.fitness_function()
        #self.fitness = self.fitness_min_steps(steps)
        return

    def fitness_function(self):
        return 1.0 / (1.0 + self._get_distance())

    def fitness_min_steps(self, steps):
        return self.fitness_function() - steps

    def get_neighbours(self):
        neighbours = []

        deltas = [(0, 1), (0, -1), (1, 0), (-1, 0), (-1, 1), (1, -1), (1, 1), (-1, -1)]
        for delta in deltas:
            try:
                neighbours.append(0 if self.map[self.pos_x + delta[0]][self.pos_y + delta[1]] == 0 or 'E' or 'S' else 1)
            except IndexError:
                neighbours.append(1)

        return neighbours

# Creates agents with the given net and tests it on the given map
def eval_genomes(genomes, config):
    """
        Testet jedes Genom mit einem Agenten.
    """
    
    map = config.map
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        agent = Agent(net)
        agent.set_map(map)
        agent.set_start(0,0)
        agent.set_goal(MAP_SIZE-1, MAP_SIZE-1)
        agent.run()
        genome.fitness = agent.fitness

    return

# Erzeugen einer Zufallskarte der Größe 20x20
generator = MapGenerator(MAP_SIZE, (0, 0), (MAP_SIZE-1, MAP_SIZE-1))
generator.generate()

# Laden einer geeigneten NEAT-Konfiguration aus der Datei 'neat-config'
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     'neat-config')
config.map = generator.map

# Erzeugen einer Population
p = neat.Population(config)

# Ein Listener, der den Status auf der Konsole loggt
p.add_reporter(neat.StdOutReporter(False))

# Statistik-Logger für die Visualisierung des Netzes
stats = neat.StatisticsReporter()
p.add_reporter(stats)

# Run until a solution is found.
winner = p.run(eval_genomes, 10) # up to X generations

#visualize.draw_net(config, winner, True)
#visualize.draw_net(config, winner, True, prune_unused=True)
#visualize.plot_stats(stats, ylog=False, view=True)
#visualize.plot_species(stats, view=True)

net = neat.nn.FeedForwardNetwork.create(winner, config)
agent = Agent(net)
agent.set_map(config.map)
agent.set_goal(MAP_SIZE-1, MAP_SIZE-1)
agent.set_start(0,0)
#agent.visited = {(0, 0)}  # Startposition als besucht markieren
generator.draw_map(agent)