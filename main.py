import pygame
import random
import sys
import math
import neat # импорт нужных библиотек, нит это нейросеть

width = 1300
height = 1100 # размеры окна
bg = (213,193,154,255) #цвет бэкграунда

generation = 0

class Car:

	car_sprites = ("Audi", "Black_viper", "Orange", "Police", "Taxi") # список спрайтов машин

	def __init__(self): # конструктор
		self.random_sprite()

		self.angle = 0
		self.speed = 5

		self.radars = []
		self.collision_points = []

		self.is_alive = True
		self.goal = False
		self.distance = 0
		self.time_spent = 0

	def random_sprite(self): # рандомит спрайт машины, определяет положение машины
		self.car_sprite = pygame.image.load('sprites/' + random.choice(self.car_sprites) + '.png')
		self.car_sprite = pygame.transform.scale(self.car_sprite,
			(math.floor(self.car_sprite.get_size()[0]/2), math.floor(self.car_sprite.get_size()[1]/2)))
		self.car = self.car_sprite

		self.pos = [650, 930]
		self.compute_center()

	def compute_center(self): # определяет центр
		self.center = (self.pos[0] + (self.car.get_size()[0]/2), self.pos[1] + (self.car.get_size()[1] / 2))

	def draw(self, screen): # отрисовывает машину и запускает прорисовку радаров
		screen.blit(self.car, self.pos)
		self.draw_radars(screen)

	def draw_center(self, screen): # отрисовывает центр машины
		pygame.draw.circle(screen, (0,72,186), (math.floor(self.center[0]), math.floor(self.center[1])), 5)

	def draw_radars(self, screen): # рисует радары
		for r in self.radars:
			p, d = r
			pygame.draw.line(screen, (183,235,70), self.center, p, 1)
			pygame.draw.circle(screen, (183,235,70), p, 5)

	def compute_radars(self, degree, road): # создает радары
		length = 0
		x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
		y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

		while not road.get_at((x, y)) == bg and length < 300: # просчет длины радаров пока не столкнулся со стеной
			length = length + 1
			x = int(self.center[0] + math.cos(math.radians(360 - (self.angle + degree))) * length)
			y = int(self.center[1] + math.sin(math.radians(360 - (self.angle + degree))) * length)

		dist = int(math.sqrt(math.pow(x - self.center[0], 2) + math.pow(y - self.center[1], 2)))
		self.radars.append([(x, y), dist])

	def compute_collision_points(self): # создание точек коллизий
		self.compute_center()
		lw = 65
		lh = 65

		lt = [self.center[0] + math.cos(math.radians(360 - (self.angle + 20))) * lw, self.center[1] + math.sin(math.radians(360 - (self.angle + 20))) * lh]
		rt = [self.center[0] + math.cos(math.radians(360 - (self.angle + 160))) * lw, self.center[1] + math.sin(math.radians(360 - (self.angle + 160))) * lh]
		lb = [self.center[0] + math.cos(math.radians(360 - (self.angle + 200))) * lw, self.center[1] + math.sin(math.radians(360 - (self.angle + 200))) * lh]
		rb = [self.center[0] + math.cos(math.radians(360 - (self.angle + 340))) * lw, self.center[1] + math.sin(math.radians(360 - (self.angle + 340))) * lh]

		self.collision_points = [lt, rt, lb, rb]

	def draw_collision_points(self, road, screen): # прорисовка точек коллизий
		if not self.collision_points:
			self.compute_collision_points()

		for p in self.collision_points: # красит точки от положения
			if(road.get_at((int(p[0]), int(p[1]))) == bg):
				pygame.draw.circle(screen, (255,0,0), (int(p[0]), int(p[1])), 5)
			else:
				pygame.draw.circle(screen, (15,192,252), (int(p[0]), int(p[1])), 5)

	def check_collision(self, road): # проверяет все ли точки на дороге
		self.is_alive = True

		for p in self.collision_points:
			try:
				if road.get_at((int(p[0]), int(p[1]))) == bg:
					self.is_alive = False
					break
			except IndexError:
				self.is_alive = False

	def rotate(self, angle): # поворот спрайта за машиной
		orig_rect = self.car_sprite.get_rect()
		rot_image = pygame.transform.rotate(self.car_sprite, angle)
		rot_rect = orig_rect.copy()
		rot_rect.center = rot_image.get_rect().center
		rot_image = rot_image.subsurface(rot_rect).copy()

		self.car = rot_image

	def get_data(self): # входящие данные для нейросети
		radars = self.radars
		data = [0, 0, 0, 0, 0]

		for i, r in enumerate(radars):
			data[i] = int(r[1] / 30)

		return data

	def get_reward(self): # награда для нейросети
		return self.distance / 50.0

	def update(self, road): # обновление всевозможных позиций
		# скорость
		self.speed = 5

		# угол поворота
		self.rotate(self.angle)

		# движение
		self.pos[0] += math.cos(math.radians(360 - self.angle)) * self.speed
		if self.pos[0] < 20:
			self.pos[0] = 20
		elif self.pos[0] > width - 120:
			self.pos[0] = width - 120

		self.pos[1] += math.sin(math.radians(360 - self.angle)) * self.speed
		if self.pos[1] < 20:
			self.pos[1] = 20
		elif self.pos[1] > height - 120:
			self.pos[1] = height - 120

		# обновление дистанции и времени
		self.distance += self.speed
		self.time_spent += 1 # aka turns

		# проверка коллизий и создание радаров
		self.compute_collision_points()
		self.check_collision(road)

		self.radars.clear()
		for d in range(-90, 120, 45):
			self.compute_radars(d, road)

start = False

def run_generation(genomes, config):

	nets = []
	cars = []

	# создание геномов
	for i, g in genomes:
		net = neat.nn.FeedForwardNetwork.create(g, config)
		nets.append(net)
		g.fitness = 0 # каждый геном на старте не успешен

		# создание машин
		cars.append(Car())

	# инициация игры
	pygame.init()
	screen = pygame.display.set_mode((width, height))
	clock = pygame.time.Clock()
	road = pygame.image.load('sprites/road.png')

	font = pygame.font.SysFont("Roboto", 40)
	heading_font = pygame.font.SysFont("Roboto", 80)

	# цикл для машин
	global generation
	global start
	generation += 1

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit(0)
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					start = True

		if not start:
			continue

		# данные для машин
		for i, car in enumerate(cars):
			output = nets[i].activate(car.get_data())
			i = output.index(max(output))

			if i == 0:
				car.angle += 5
			elif i == 1:
				car.angle = car.angle
			elif i == 2:
				car.angle -= 5

		# обновляем машины и для живых выдаем награду
		cars_left = 0
		for i, car in enumerate(cars):
			if car.is_alive:
				cars_left += 1
				car.update(road)
				genomes[i][1].fitness += car.get_reward()

		# проверяем наличие живых машин
		if not cars_left:
			break

		# отображаем все
		screen.blit(road, (0, 0))

		for car in cars:
			if car.is_alive:
				car.draw(screen)
				car.draw_center(screen)
				car.draw_collision_points(road, screen)

		label = heading_font.render("Поколение: " + str(generation), True, (73,168,70))
		label_rect = label.get_rect()
		label_rect.center = (width / 1.5, 300)
		screen.blit(label, label_rect)

		label = font.render("Машин осталось: " + str(cars_left), True, (51,59,70))
		label_rect = label.get_rect()
		label_rect.center = (width / 1.5, 375)
		screen.blit(label, label_rect)

		pygame.display.flip()
		clock.tick(0)

if __name__ == "__main__":
	# задаем конфиг
	config_path = "./config-feedforward.txt"
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

	# создаем NEAT
	p = neat.Population(config)

	# запуск NEAT
	p.run(run_generation, 1000)