import pygame
import os
import random
from enum import Enum
import json
import uuid
from threading import Thread

import pika



pygame.init()
pygame.mixer.init()
SCREEN_W = 800
SCREEN_H = 600


my_bullet_sprite = pygame.image.load("bullet1_sprite.png")#.convert()
my_bullet_sprite = pygame.transform.scale(my_bullet_sprite, (15, 5))
my_bullet_sprite.set_colorkey((255, 255, 255))
my_bullet_sprite_UP = pygame.transform.rotate(my_bullet_sprite, 90)
my_bullet_sprite_LEFT = pygame.transform.rotate(my_bullet_sprite, 180)
my_bullet_sprite_DOWN = pygame.transform.rotate(my_bullet_sprite, 270)



bullet1_sprite = pygame.image.load("bullet2_sprite.png")#.convert()
bullet1_sprite = pygame.transform.scale(bullet1_sprite, (15, 5))
bullet1_sprite.set_colorkey((255, 255, 255))
bullet1_sprite_UP = pygame.transform.rotate(bullet1_sprite, 90)
bullet1_sprite_LEFT = pygame.transform.rotate(bullet1_sprite, 180)
bullet1_sprite_DOWN = pygame.transform.rotate(bullet1_sprite, 270)


my_tank_sprite = pygame.image.load("tank1_sprite.png")#.convert()
my_tank_sprite = pygame.transform.scale(my_tank_sprite, (35, 35))
my_tank_sprite.set_colorkey((255, 255, 255))
my_tank_sprite_UP = pygame.transform.rotate(my_tank_sprite, 90)
my_tank_sprite_LEFT = pygame.transform.rotate(my_tank_sprite, 180)
my_tank_sprite_DOWN = pygame.transform.rotate(my_tank_sprite, 270)


tank_sprite = pygame.image.load("tank2_sprite.png")#.convert()
tank_sprite = pygame.transform.scale(tank_sprite, (35, 35))
tank_sprite.set_colorkey((255, 255, 255))

tank_sprite_UP = pygame.transform.rotate(tank_sprite, 90)
tank_sprite_LEFT = pygame.transform.rotate(tank_sprite, 180)
tank_sprite_DOWN = pygame.transform.rotate(tank_sprite, 270)




class TankRpcClient:
    global MY_TANK_ID

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=IP,
                port=PORT,
                virtual_host=VIRTUAL_HOST,
                credentials=pika.PlainCredentials(
                    username=USERNAME,
                    password=PASSWORD
                )
            )
        )
        self.channel = self.connection.channel()
        queue = self.channel.queue_declare(queue='',
                                           auto_delete=True,
                                           exclusive=True
                                           )
        self.callback_queue = queue.method.queue
        self.channel.queue_bind(
            exchange='X:routing.topic',
            queue=self.callback_queue
        )

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )
        self.response = None
        self.corr_id = None
        self.token = None
        self.tank_id = None
        self.room_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)
            print(self.response)

    def call(self, key, message={}):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='X:routing.topic',
            routing_key=key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(message)
        )
        while self.response is None:
            self.connection.process_data_events()

    def check_server_status(self):
        self.call('tank.request.healthcheck')
        return self.response['status'] == '200'

    def obtain_token(self, room_id):
        global MY_TANK_ID
        message = {
            'roomId': room_id
        }
        self.call('tank.request.register', message)
        if 'token' in self.response:
            self.token = self.response['token']
            self.tank_id = self.response['tankId']
            MY_TANK_ID = self.tank_id
            self.room_id = self.response['roomId']
            return True
        return False
    def turn_tank(self, token, direction):
        message = {
            'token': token,
            'direction': direction
        }
        self.call('tank.request.turn', message)

    def fire_bullet(self, token):
        message = {
            'token': token
        }
        self.call('tank.request.fire', message)

class TankConsumerClient(Thread):

    def __init__(self, room_id):
        super().__init__()
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=IP,
                port=PORT,
                virtual_host=VIRTUAL_HOST,
                credentials=pika.PlainCredentials(
                    username=USERNAME,
                    password=PASSWORD
                )
            )
        )
        self.channel = self.connection.channel()
        queue = self.channel.queue_declare(queue='',
                                           auto_delete=True,
                                           exclusive=True
                                           )
        #self.listener = queue.method.queue
        event_listener = queue.method.queue
        self.channel.queue_bind(exchange='X:routing.topic',
                                queue=event_listener,
                                routing_key='event.state.'+room_id)


        self.channel.basic_consume(
            queue=event_listener,
            on_message_callback=self.on_response,
            auto_ack=True
         )
        self.response = None

    def on_response(self, ch, method, props, body):
        self.response = json.loads(body)

    def run(self):
        self.channel.start_consuming()

UP = 'UP'
DOWN = 'DOWN'
LEFT = 'LEFT'
RIGHT = 'RIGHT'

MOVE_KEYS = {
    pygame.K_w: UP,
    pygame.K_a: LEFT,
    pygame.K_s: DOWN,
    pygame.K_d: RIGHT
}




font = pygame.font.Font('freesansbold.ttf', 32)
font2 = pygame.font.Font('freesansbold.ttf', 15)

background = pygame.image.load("background.jpg")#.convert()
background = pygame.transform.scale(background, (SCREEN_W - 200, SCREEN_H))
FPS = 60
clock = pygame.time.Clock()




IP = '34.254.177.17'
PORT = '5672'
VIRTUAL_HOST = 'dar-tanks'
USERNAME = 'dar-tanks'
PASSWORD = '5orPLExUYnyVYZg48caMpX'
MY_TANK_ID = ''
MY_SCORE = ''







wall_sprite = pygame.image.load("wall_sprite.png")#.convert()
wall_sprite.set_colorkey((255, 255, 255))

sound_shoot = pygame.mixer.Sound('sound_shoot.wav')


buff_sprite = pygame.image.load("buff_sprite.png")#.convert()
buff_sprite.set_colorkey((255, 255, 255))

class Buff:
    def __init__(self, x, y):
        self.size = 40 # in px
        self.x = x
        self.y = y

        self.sprite = buff_sprite
        self.sprite = pygame.transform.scale(self.sprite, (self.size, self.size))


    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))


class Bullet:

    def __init__(self, tank, speed, screen):
        sound_shoot.play()
        self.screen = screen
        self.size = 2
        self.tank = tank
        self.sprite = tank.bullet_sprite
        self.direction = tank.direction
        self.speed = speed
        self.life_time = 0
        self.del_time = 1.5 # in sec

        self.bullet_w = 15
        self.bullet_h = 5

        self.sprite_RIGHT = self.sprite
        self.sprite_UP = pygame.transform.rotate(self.sprite, 90)
        self.sprite_LEFT = pygame.transform.rotate(self.sprite, 180)
        self.sprite_DOWN = pygame.transform.rotate(self.sprite, 270)

        if tank.direction == Direction.RIGHT:
            self.sprite = tank.bullet_sprite
            self.x = tank.x + tank.height + int(tank.height / 2)
            self.y = int(tank.y + tank.width / 2)
        if self.direction == Direction.LEFT:
            self.sprite = pygame.transform.rotate(self.sprite, 180)
            self.x = tank.x - tank.height + int(tank.height / 2)
            self.y = tank.y + int(tank.width / 2)
        if self.direction == Direction.UP:
            self.sprite = pygame.transform.rotate(self.sprite, 90)
            self.x = tank.x + int(tank.height / 2)
            self.y = tank.y - int(tank.width / 2)
        if self.direction == Direction.DOWN:
            self.sprite = pygame.transform.rotate(self.sprite, 270)
            self.x = tank.x + int(tank.height / 2)
            self.y = tank.y + tank.width + int(tank.width / 2)

    def draw(self):
        #pygame.draw.circle(self.screen, self.color, (self.x, self.y), self.size)
        self.screen.blit(self.sprite, (self.x , self.y))

    def move(self, seconds):
        self.life_time += seconds

        if self.direction == Direction.RIGHT:
            self.x += int(self.speed * seconds)
        if self.direction == Direction.LEFT:
            self.x -= int(self.speed * seconds)
        if self.direction == Direction.UP:
            self.y -= int(self.speed * seconds)
        if self.direction == Direction.DOWN:
            self.y += int(self.speed * seconds)



class Wall:

    def __init__(self, x, y):
        self.size = 40 # in px
        self.x = x
        self.y = y

        self.sprite = wall_sprite
        self.sprite = pygame.transform.scale(self.sprite, (self.size, self.size))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))



class Tank:

    def __init__(self, x, y, speed, sprite, bullet_sprite, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP,
                 d_down=pygame.K_DOWN, fire_key=pygame.K_RETURN):
        self.buff = False
        self.buff_time = 0

        self.num_of_bullet = 3
        self.fire_key = fire_key
        self.recharge = False
        self.recharge_duration = 2 # in sec
        self.recharge_time = 0 # in sec

        self.lifes = 3
        self.x = x
        self.y = y
        self.speed = speed

        #self.color = color
        self.bullet_sprite = bullet_sprite

        self.sprite = sprite
        self.sprite_RIGHT = self.sprite
        self.sprite_UP = pygame.transform.rotate(self.sprite, 90)
        self.sprite_LEFT = pygame.transform.rotate(self.sprite, 180)
        self.sprite_DOWN = pygame.transform.rotate(self.sprite, 270)

        self.width = 35
        self.height = 35
        self.direction = Direction.RIGHT

        self.KEY = {
            d_right: Direction.RIGHT,
            d_left: Direction.LEFT,
            d_up: Direction.UP,
            d_down: Direction.DOWN
        }

    def draw(self, screen, size_w, size_h):
        tank_c = (self.x + int(self.width / 2), self.y + int(self.height / 2))

        if self.x <= 0:
            self.x = size_w - self.width
        if self.y <= 0:
            self.y = size_h - self.height
        if self.x + self.width > size_w:
            self.x = 0
        if self.y >= size_h:
            self.y = 0

        #screen.blit(self.sprite, (self.x, self.y))

        # pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 2)
        # pygame.draw.circle(screen, self.color, tank_c, int(self.width / 2))

        if self.direction == Direction.RIGHT:
              screen.blit(self.sprite_RIGHT, (self.x, self.y))

              for i in range(0, self.lifes):
                  r = int(((self.width / 3) / 2) - 2)
                  pygame.draw.circle(screen, (0, 255, 0), (2 * r + self.x + i * 3 * r, self.y + r - 2), r)
        #     pygame.draw.line(screen, self.color, tank_c,
        #                      (self.x + self.height + int(self.height / 2), int(self.y + self.width / 2)), 4)
        if self.direction == Direction.LEFT:
              screen.blit(self.sprite_LEFT, (self.x, self.y))

              for i in range(0, self.lifes):
                  r = int(((self.width / 3) / 2) - 2)
                  pygame.draw.circle(screen, (0, 255, 0), (2 * r + self.x + i * 3 * r + 4, self.y + r - 4), r)
        #     pygame.draw.line(screen, self.color, tank_c,
        #                      (self.x - self.height + int(self.height / 2), self.y + int(self.width / 2)), 4)
        if self.direction == Direction.UP:
              screen.blit(self.sprite_UP, (self.x, self.y))

              for i in range(0, self.lifes):
                  r = int(((self.width / 3) / 2) - 2)
                  pygame.draw.circle(screen, (0, 255, 0), (2 * r + self.x + i * 3 * r + 3, self.y + r + self.width - 2), r)
        #     pygame.draw.line(screen, self.color, tank_c, (self.x + int(self.height / 2), self.y - int(self.width / 2)),
        #                      4)
        if self.direction == Direction.DOWN:
              screen.blit(self.sprite_DOWN, (self.x, self.y))

              for i in range(0, self.lifes):
                  r = int(((self.width / 3) / 2) - 2)
                  pygame.draw.circle(screen, (0, 255, 0), (2 * r + self.x + i * 3 * r + 1, self.y + r - 4), r)
        #     pygame.draw.line(screen, self.color, tank_c,
        #                      (self.x + int(self.height / 2), self.y + self.width + int(self.width / 2)), 4)



    def change_direction(self, direction):
        self.direction = direction

    def move(self, seconds):
        if self.direction == Direction.LEFT:
            self.x -= int(self.speed * seconds)
        if self.direction == Direction.RIGHT:
            self.x += int(self.speed * seconds)
        if self.direction == Direction.UP:
            self.y -= int(self.speed * seconds)
        if self.direction == Direction.DOWN:
            self.y += int(self.speed * seconds)

        self.recharge_time += seconds
        if self.recharge_time >= self.recharge_duration:
            self.recharge = False
            self.recharge_time = 0





class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Button:

    def __init__(self, x, y, text, func):
        self.x = x
        self.y = y
        self.text = text
        self.func = func

    def draw(self, screen):
        font = pygame.font.Font('freesansbold.ttf', 28)
        text = font.render(self.text, True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (self.x, self.y)
        screen.blit(text, textRect)









WHICH_ROOM = 1




screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
menu_background = pygame.image.load("menu_background.png").convert()
menu_background = pygame.transform.scale(menu_background, (SCREEN_W, SCREEN_H))


MAIN_MENU = True
SINGLE_PLAY = False
MULTI_PLAY = False
MULTI_AI_PLAY = False

def click_button_single():
    global MAIN_MENU, SINGLE_PLAY, MULTI_PLAY, MULTI_AI_PLAY
    #os.startfile('main.py')
    SINGLE_PLAY = True
    MAIN_MENU = False
def click_button_multi():
    global MAIN_MENU, SINGLE_PLAY, MULTI_PLAY, MULTI_AI_PLAY
    #os.startfile('multi_main.py')
    MULTI_PLAY = True
    MAIN_MENU = False
def click_button_multi_AI():
    global MAIN_MENU, SINGLE_PLAY, MULTI_PLAY, MULTI_AI_PLAY
    #print('ok good MULTI AI')
    MULTI_AI_PLAY = True
    MAIN_MENU = False



button_single = Button(410, 350, "Одиночная игра", click_button_single)
button_multi = Button(130, 350,"Мультиплеер", click_button_multi)
button_multi_AI = Button(670, 350,"Мультиплеер ИИ", click_button_multi_AI)


buttons = [button_single, button_multi, button_multi_AI]


rooms = []
room_num = 1
for i in range(1, 7):
    for j in range(1,6):
        text = 'room: {}'.format(room_num)
        rooms.append(Button(j * 160 - 80, i * 100 - 50, text, room_num))
        room_num += 1



run = True

while run:
    if MAIN_MENU:
        pos = pygame.mouse.get_pos()

        screen.blit(menu_background, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False


            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if button.x - 100 <= pos[0] <= button.x + 100 and button.y - 20 <= pos[1] <= button.y + 20:
                        button.func()

        for button in buttons:
            button.draw(screen)

        pygame.display.flip()
    elif SINGLE_PLAY:

        background = pygame.image.load("background.jpg").convert()
        background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
        FPS = 60
        clock = pygame.time.Clock()
        sound_hit = pygame.mixer.Sound('sound_hit.wav')
        tank1_sprite = pygame.image.load("tank1_sprite.png").convert()
        tank1_sprite = pygame.transform.scale(tank1_sprite, (35, 35))
        tank1_sprite.set_colorkey((255, 255, 255))
        tank2_sprite = pygame.image.load("tank2_sprite.png").convert()
        tank2_sprite = pygame.transform.scale(tank2_sprite, (35, 35))
        tank2_sprite.set_colorkey((255, 255, 255))
        bullet1_sprite = pygame.image.load("bullet1_sprite.png").convert()
        bullet1_sprite = pygame.transform.scale(bullet1_sprite, (15, 5))
        bullet1_sprite.set_colorkey((255, 255, 255))
        bullet2_sprite = pygame.image.load("bullet2_sprite.png").convert()
        bullet2_sprite = pygame.transform.scale(bullet2_sprite, (15, 5))
        bullet2_sprite.set_colorkey((255, 255, 255))

        running = True
        tank_1 = Tank(300, 300, 200, tank1_sprite, bullet1_sprite)
        tank_2 = Tank(100, 100, 200, tank2_sprite, bullet2_sprite, pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s,
                      pygame.K_SPACE)

        tanks = [tank_1, tank_2]
        bullets = []


        def hit_check(bullet, which_bullet):
            global tanks

            shadow_x1 = []
            shadow_x2 = []
            shadow_y1 = []
            shadow_y2 = []
            i = 0
            for tank in tanks:
                shadow_x1.append(tank.x)
                shadow_x2.append(tank.x + tank.width)
                shadow_y1.append(tank.y)
                shadow_y2.append(tank.y + tank.height)

                if shadow_x1[i] <= bullet.x <= shadow_x2[i] and shadow_y1[i] <= bullet.y <= shadow_y2[i]:
                    sound_hit.play()

                    tank.lifes -= 1
                    if tank.lifes <= 0: del tanks[i]
                    del bullets[which_bullet]

                i += 1


        wallprob = Wall(1000, 1000)
        walls = []

        for i in range(0, SCREEN_H, wallprob.size):
            for j in range(0, SCREEN_W, wallprob.size):
                rand = random.randint(1, 100)
                if rand <= 10:
                    walls.append(Wall(j, i))

        buffs = []
        buff_time = 0
        buff_time_when = random.randint(1, 10)

        while running:
            millis = clock.tick(FPS)
            seconds = millis / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    for tank in tanks:
                        if event.key in tank.KEY.keys():
                            tank.change_direction(tank.KEY[event.key])
                        if event.key == tank.fire_key:
                            if tank.recharge != True:
                                if tank.buff == False:
                                    bullets.append(Bullet(tank, 500, screen))
                                else:
                                    bullets.append(Bullet(tank, 1000, screen))
                                tank.recharge = True

            screen.blit(background, (0, 0))

            for tank in tanks:

                i = 0
                for wall in walls:
                    x1 = wall.x
                    y1 = wall.y
                    x2 = wall.x + wall.size
                    y2 = wall.y + wall.size

                    if (((tank.x <= x2 and tank.x >= x1) or (
                            tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (
                                tank.y <= y2 and tank.y >= y1)) or (((tank.x <= x2 and tank.x >= x1) or (
                            tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (
                                                                            tank.y + tank.width <= y2 and tank.y + tank.width >= y1)):
                        tank.lifes -= 1
                        del walls[i]
                    i += 1

                i = 0
                for buff in buffs:
                    x1 = buff.x
                    y1 = buff.y
                    x2 = buff.x + buff.size
                    y2 = buff.y + buff.size

                    if (((tank.x <= x2 and tank.x >= x1) or (
                            tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (
                                tank.y <= y2 and tank.y >= y1)) or (((tank.x <= x2 and tank.x >= x1) or (
                            tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (
                                                                            tank.y + tank.width <= y2 and tank.y + tank.width >= y1)):
                        tank.buff = True
                        del buffs[i]

                tank.move(seconds)
                tank.draw(screen, SCREEN_W, SCREEN_H)

            i = 0
            for bullet in bullets:
                hit_check(bullet, i)
                bullet.move(seconds)
                bullet.draw()
                if bullet.life_time >= bullet.del_time: del bullets[i]
                i += 1

            k = 0
            for wall in walls:
                x1 = wall.x
                y1 = wall.y
                x2 = wall.x + wall.size
                y2 = wall.y + wall.size
                ktmp = 0
                for bullet in bullets:
                    if (((bullet.x <= x2 and bullet.x >= x1) or (
                            bullet.x + bullet.bullet_h <= x2 and bullet.x + bullet.bullet_h >= x1)) and (
                                bullet.y <= y2 and bullet.y >= y1)) or (
                            ((bullet.x <= x2 and bullet.x >= x1) or (
                                    bullet.x + bullet.bullet_h <= x2 and bullet.x + bullet.bullet_h >= x1)) and (
                                    bullet.y + bullet.bullet_h <= y2 and bullet.y + bullet.bullet_h >= y1)):
                        del walls[k]
                        del bullets[ktmp]
                    ktmp += 1
                k += 1

                wall.draw(screen)

            buff_time += seconds
            if buff_time >= buff_time_when:
                buff_time = 0
                buff_time_when = random.randint(1, 10)
                buff_x, buff_y = 0, 0
                wrong = False
                while not wrong:
                    buff_x = random.randint(0, SCREEN_W / wallprob.size)
                    buff_y = random.randint(0, SCREEN_H / wallprob.size)
                    for wall in walls:
                        if wall.x != buff_x * wallprob.size and wall.y != buff_y * wallprob.size:
                            wrong = True

                buffs.append(Buff(buff_x * wallprob.size, buff_y * wallprob.size))

            for buff in buffs:
                buff.draw(screen)

            for tank in tanks:
                if tank.buff == True and tank.buff_time <= 5:
                    tank.speed = 400
                    tank.buff_time += seconds
                else:
                    tank.buff = False
                    tank.buff_time = 0
                    tank.speed = 200

            ######tests######
            screen.blit(tank1_sprite, (0, 0))
            # wall.draw(screen)
            ################

            # print(seconds)
            pygame.display.flip()

        #os.startfile('main.py')
        SINGLE_PLAY = False
        MAIN_MENU = True
        #run = False
    else:
        pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                MAIN_MENU = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    MAIN_MENU = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                for room in rooms:
                    if room.x - 50 <= pos[0] <= room.x + 50 and room.y - 20 <= pos[1] <= room.y + 20:
                        WHICH_ROOM = room.func
                        #run = False
                        if MULTI_PLAY:
                            SCREEN_W = 1000
                            background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
                            screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

                            def draw_tank(x, y, width, height, direction, tank_id, tank_health):
                                global MY_TANK_ID, font2, screen, my_tank_sprite, my_tank_sprite_DOWN, my_tank_sprite_LEFT, my_tank_sprite_UP

                                if tank_id == MY_TANK_ID:
                                    if direction == 'RIGHT':
                                        screen.blit(my_tank_sprite, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)
                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2),
                                                               r)

                                    if direction == 'LEFT':
                                        screen.blit(my_tank_sprite_LEFT, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 4, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'UP':
                                        screen.blit(my_tank_sprite_UP, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 3, y + r + width),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'DOWN':
                                        screen.blit(my_tank_sprite_DOWN, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 1, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                else:
                                    if direction == 'RIGHT':
                                        screen.blit(tank_sprite, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'LEFT':
                                        screen.blit(tank_sprite_LEFT, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 4, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'UP':
                                        screen.blit(tank_sprite_UP, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 3, y + r + width),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'DOWN':
                                        screen.blit(tank_sprite_DOWN, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 1, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)


                            def draw_bullet(x, y, width, height, direction, bullet_owner):

                                if bullet_owner == MY_TANK_ID:
                                    if direction == 'RIGHT':
                                        screen.blit(my_bullet_sprite, (x, y))
                                    if direction == 'LEFT':
                                        screen.blit(my_bullet_sprite_LEFT, (x, y))
                                    if direction == 'UP':
                                        screen.blit(my_bullet_sprite_UP, (x, y))
                                    if direction == 'DOWN':
                                        screen.blit(my_bullet_sprite_DOWN, (x, y))
                                else:
                                    if direction == 'RIGHT':
                                        screen.blit(bullet1_sprite, (x, y))
                                    if direction == 'LEFT':
                                        screen.blit(bullet1_sprite_LEFT, (x, y))
                                    if direction == 'UP':
                                        screen.blit(bullet1_sprite_UP, (x, y))
                                    if direction == 'DOWN':
                                        screen.blit(bullet1_sprite_DOWN, (x, y))


                            def draw_panel(tanks):
                                global screen
                                pygame.draw.rect(screen, (0, 0, 0), ((800, 0), (200, 600)))

                                k = 0

                                max = 0
                                for tank in tanks:
                                    if tank['score'] > max:
                                        max = tank['score']

                                texttmp = font2.render('ID         LIFE       SCORE', True, (255, 255, 255))
                                texttmpRect = texttmp.get_rect()
                                texttmpRect.center = (900 + 15, 10)
                                screen.blit(texttmp, texttmpRect)

                                y = 30
                                while (max >= 0):

                                    for tank in tanks:
                                        if tank['score'] == max:
                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['id']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('i', True, (0, 255, 0))
                                            textRect = text.get_rect()
                                            textRect.center = (825 + 15, y)
                                            screen.blit(text, textRect)

                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['health']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('{}'.format(tank['health']), True, (0, 255, 0))

                                            textRect = text.get_rect()
                                            textRect.center = (825 + 90, y)
                                            screen.blit(text, textRect)

                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['score']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('{}'.format(tank['score']), True, (0, 255, 0))
                                            textRect = text.get_rect()
                                            textRect.center = (825 + 160, y)
                                            screen.blit(text, textRect)

                                            y += 30
                                            # print(tank['id'])
                                            # print(tank['health'])
                                            # print(tank['score'])

                                    max -= 1


                            def loserr():

                                global screen, MY_SCORE
                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Неудача!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)


                            def winerr():

                                global screen, MY_SCORE
                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Победа!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)


                            def game_start():
                                global MY_SCORE
                                run = True
                                global font
                                global screen
                                los = False
                                won = False
                                global MOVE_KEYS

                                while run:
                                    millis = clock.tick(FPS)
                                    seconds = millis / 1000
                                    screen.blit(background, (0, 0))

                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            run = False
                                        if event.type == pygame.KEYDOWN:
                                            if event.key == pygame.K_ESCAPE:
                                                run = False
                                            if event.key in MOVE_KEYS:
                                                client.turn_tank(client.token, MOVE_KEYS[event.key])
                                            if event.key == pygame.K_SPACE:
                                                client.fire_bullet(client.token)

                                            for event in pygame.event.get():
                                                if event.type == pygame.KEYDOWN:
                                                    if event.key == pygame.K_r:
                                                        los = False
                                                        won = False

                                    try:
                                        remaining_time = event_client.response['remainingTime']
                                        text = font.render('Remaining Time: {}'.format(remaining_time), True, (0, 0, 0))
                                        textRect = text.get_rect()
                                        screen.blit(text, textRect)
                                        if remaining_time == 0:
                                            run = False

                                        hits = event_client.response['hits']
                                        winners = event_client.response['winners']
                                        losers = event_client.response['losers']

                                        tanks = event_client.response['gameField']['tanks']
                                        bullets = event_client.response['gameField']['bullets']

                                        draw_panel(tanks)

                                        for loser in losers:
                                            if loser['tankId'] == MY_TANK_ID:
                                                # print("")
                                                los = True
                                        for win in winners:
                                            if win['tankId'] == MY_TANK_ID:
                                                won = True

                                        #         run2 = True
                                        #         while run2:
                                        #             screen.fill((255, 255, 255))
                                        #
                                        #             # for event in pygame.event.get():
                                        #             #     if event.type == pygame.KEYDOWN:
                                        #             #         if event.key == pygame.K_ESCAPE:
                                        #             #             run2 = False
                                        #
                                        #             text = font.render('self.text', True, (0, 0, 0))
                                        #             textRect = text.get_rect()
                                        #             textRect.center = (500, 500)
                                        #             screen.blit(text, textRect)
                                        #
                                        #             screen.flip()

                                        for tank in tanks:
                                            tank_x = tank['x']
                                            tank_y = tank['y']
                                            tank_width = tank['width']
                                            tank_height = tank['height']
                                            tank_direction = tank['direction']
                                            tank_id = tank['id']
                                            tank_health = tank['health']

                                            if tank['id'] == MY_TANK_ID:
                                                MY_SCORE = tank['score']

                                            # txt_losers = ','.join(i['tankId'] for i in losers)
                                            # print(txt_losers)
                                            # if tank['id'] == MY_TANK_ID: #and tank['health'] == 0:
                                            #     for lose in losers:
                                            #
                                            #             print(','.join(lose['tankId']))

                                            #    print(tank['health'])
                                            # for lose in losers:
                                            # print(lose['tankid'])
                                            #     lose(tank['score'])
                                            # print(losers)

                                            # txt_losers = ','.join(i['tankId'] for i in losers)
                                            # print(txt_losers)

                                            draw_tank(tank_x, tank_y, tank_width, tank_height, tank_direction, tank_id,
                                                      tank_health)

                                        for bullet in bullets:
                                            bullet_x = bullet['x']
                                            bullet_y = bullet['y']
                                            bullet_owner = bullet['owner']
                                            bullet_width = bullet['width']
                                            bullet_height = bullet['height']
                                            bullet_direction = bullet['direction']
                                            draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height,
                                                        bullet_direction, bullet_owner)  # if bullet_owner == my_tank_id
                                    except:
                                        pass

                                    if los:
                                        loserr()
                                    if won:
                                        winerr()

                                    pygame.display.flip()

                                client.connection.close()
                                # pygame.quit()


                            client = TankRpcClient()
                            client.check_server_status()
                            which_room = 'room-' + str(WHICH_ROOM)
                            client.obtain_token(which_room)
                            event_client = TankConsumerClient(which_room)
                            event_client.start()
                            game_start()

                            runtmp = True
                            while runtmp:

                                screen.fill((0, 0, 0))
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        runtmp = False
                                    if event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_r:
                                            runtmp = False

                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Игра закончена!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)

                                text = font.render('Нажмите R чтобы сыграть заново!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 350)
                                screen.blit(text, textRect)

                                pygame.display.flip()

                            #os.startfile('multi_main.py')
                            #MULTI_PLAY = False
                            #run = False
                        if MULTI_AI_PLAY:
                            SCREEN_W = 1000
                            background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
                            screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))


                            def draw_tank(x, y, width, height, direction, tank_id, tank_health):
                                global MY_TANK_ID, font2, screen, my_tank_sprite, my_tank_sprite_DOWN, my_tank_sprite_LEFT, my_tank_sprite_UP

                                if tank_id == MY_TANK_ID:
                                    if direction == 'RIGHT':
                                        screen.blit(my_tank_sprite, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)
                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2),
                                                               r)

                                    if direction == 'LEFT':
                                        screen.blit(my_tank_sprite_LEFT, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 4, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'UP':
                                        screen.blit(my_tank_sprite_UP, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 3, y + r + width),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'DOWN':
                                        screen.blit(my_tank_sprite_DOWN, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 1, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                else:
                                    if direction == 'RIGHT':
                                        screen.blit(tank_sprite, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'LEFT':
                                        screen.blit(tank_sprite_LEFT, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 4, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'UP':
                                        screen.blit(tank_sprite_UP, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 3, y + r + width),
                                                               r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)
                                    if direction == 'DOWN':
                                        screen.blit(tank_sprite_DOWN, (x, y))
                                        tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
                                        tank_id_textRect = tank_id_text.get_rect()
                                        tank_id_textRect.center = (x + 15, y + width + 10)
                                        screen.blit(tank_id_text, tank_id_textRect)

                                        for i in range(0, tank_health):
                                            r = int(((width / 3) / 2) - 2)
                                            pygame.draw.circle(screen, (0, 255, 0),
                                                               (2 * r + x + i * 3 * r + 1, y + r - 4), r)
                                        # tank_id_textRect.center = (x, y)
                                        # screen.blit(tank_id_text, tank_id_textRect)


                            def draw_bullet(x, y, width, height, direction, bullet_owner):

                                if bullet_owner == MY_TANK_ID:
                                    if direction == 'RIGHT':
                                        screen.blit(my_bullet_sprite, (x, y))
                                    if direction == 'LEFT':
                                        screen.blit(my_bullet_sprite_LEFT, (x, y))
                                    if direction == 'UP':
                                        screen.blit(my_bullet_sprite_UP, (x, y))
                                    if direction == 'DOWN':
                                        screen.blit(my_bullet_sprite_DOWN, (x, y))
                                else:
                                    if direction == 'RIGHT':
                                        screen.blit(bullet1_sprite, (x, y))
                                    if direction == 'LEFT':
                                        screen.blit(bullet1_sprite_LEFT, (x, y))
                                    if direction == 'UP':
                                        screen.blit(bullet1_sprite_UP, (x, y))
                                    if direction == 'DOWN':
                                        screen.blit(bullet1_sprite_DOWN, (x, y))


                            def draw_panel(tanks):
                                global screen
                                pygame.draw.rect(screen, (0, 0, 0), ((800, 0), (200, 600)))

                                k = 0

                                max = 0
                                for tank in tanks:
                                    if tank['score'] > max:
                                        max = tank['score']

                                texttmp = font2.render('ID         LIFE       SCORE', True, (255, 255, 255))
                                texttmpRect = texttmp.get_rect()
                                texttmpRect.center = (900 + 15, 10)
                                screen.blit(texttmp, texttmpRect)

                                y = 30
                                while (max >= 0):

                                    for tank in tanks:
                                        if tank['score'] == max:
                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['id']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('i', True, (0, 255, 0))
                                            textRect = text.get_rect()
                                            textRect.center = (825 + 15, y)
                                            screen.blit(text, textRect)

                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['health']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('{}'.format(tank['health']), True, (0, 255, 0))

                                            textRect = text.get_rect()
                                            textRect.center = (825 + 90, y)
                                            screen.blit(text, textRect)

                                            if tank['id'] != MY_TANK_ID:
                                                text = font2.render('{}'.format(tank['score']), True, (255, 0, 0))
                                            else:
                                                text = font2.render('{}'.format(tank['score']), True, (0, 255, 0))
                                            textRect = text.get_rect()
                                            textRect.center = (825 + 160, y)
                                            screen.blit(text, textRect)

                                            y += 30
                                            # print(tank['id'])
                                            # print(tank['health'])
                                            # print(tank['score'])

                                    max -= 1


                            def loserr():

                                global screen, MY_SCORE
                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Неудача!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)


                            def winerr():

                                global screen, MY_SCORE
                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Победа!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)



                            def game_start():
                                global MY_SCORE
                                run = True
                                global font
                                global screen
                                los = False
                                won = False
                                global MOVE_KEYS

                                while run:
                                    millis = clock.tick(FPS)
                                    seconds = millis / 1000
                                    screen.blit(background, (0, 0))



                                    try:
                                        remaining_time = event_client.response['remainingTime']
                                        text = font.render('Remaining Time: {}'.format(remaining_time), True, (0, 0, 0))
                                        textRect = text.get_rect()
                                        screen.blit(text, textRect)
                                        if remaining_time == 0:
                                            run = False

                                        hits = event_client.response['hits']
                                        winners = event_client.response['winners']
                                        losers = event_client.response['losers']

                                        tanks = event_client.response['gameField']['tanks']
                                        bullets = event_client.response['gameField']['bullets']

                                        draw_panel(tanks)

                                        for loser in losers:
                                            if loser['tankId'] == MY_TANK_ID:
                                                # print("")
                                                los = True
                                        for win in winners:
                                            if win['tankId'] == MY_TANK_ID:
                                                won = True

                                        #         run2 = True
                                        #         while run2:
                                        #             screen.fill((255, 255, 255))
                                        #
                                        #             # for event in pygame.event.get():
                                        #             #     if event.type == pygame.KEYDOWN:
                                        #             #         if event.key == pygame.K_ESCAPE:
                                        #             #             run2 = False
                                        #
                                        #             text = font.render('self.text', True, (0, 0, 0))
                                        #             textRect = text.get_rect()
                                        #             textRect.center = (500, 500)
                                        #             screen.blit(text, textRect)
                                        #
                                        #             screen.flip()
                                        MY_X = 0
                                        MY_Y = 0
                                        for tank in tanks:
                                            tank_x = tank['x']
                                            tank_y = tank['y']
                                            tank_width = tank['width']
                                            tank_height = tank['height']
                                            tank_direction = tank['direction']
                                            tank_id = tank['id']
                                            tank_health = tank['health']

                                            if tank['id'] == MY_TANK_ID:
                                                MY_SCORE = tank['score']
                                                MY_X = tank['x']
                                                MY_Y = tank['y']


                                            # txt_losers = ','.join(i['tankId'] for i in losers)
                                            # print(txt_losers)
                                            # if tank['id'] == MY_TANK_ID: #and tank['health'] == 0:
                                            #     for lose in losers:
                                            #
                                            #             print(','.join(lose['tankId']))

                                            #    print(tank['health'])
                                            # for lose in losers:
                                            # print(lose['tankid'])
                                            #     lose(tank['score'])
                                            # print(losers)

                                            # txt_losers = ','.join(i['tankId'] for i in losers)
                                            # print(txt_losers)

                                            draw_tank(tank_x, tank_y, tank_width, tank_height, tank_direction, tank_id,
                                                      tank_health)

                                        for bullet in bullets:
                                            bullet_x = bullet['x']
                                            bullet_y = bullet['y']
                                            bullet_owner = bullet['owner']
                                            bullet_width = bullet['width']
                                            bullet_height = bullet['height']
                                            bullet_direction = bullet['direction']
                                            draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height,
                                                        bullet_direction, bullet_owner)  # if bullet_owner == my_tank_id
                                    except:
                                        pass




                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            run = False


                                        for event in pygame.event.get():
                                            if event.type == pygame.KEYDOWN:
                                                if event.key == pygame.K_r:
                                                    los = False
                                                    won = False


                                        if event.type == pygame.KEYDOWN:
                                            if event.key == pygame.K_ESCAPE:
                                                run = False
                                            # if event.key in MOVE_KEYS:
                                            #     client.turn_tank(client.token, MOVE_KEYS[event.key])
                                            # if event.key == pygame.K_SPACE:
                                            #     client.fire_bullet(client.token)




                                    # so_close_x = MY_X
                                    # so_close_y = MY_Y
                                    # so_close_x_tmp = 0
                                    # so_close_y_tmp = 0
                                    #
                                    # so_close_tank_id = ''
                                    # for tank in tanks:
                                    #     if tank['id'] != MY_TANK_ID:
                                    #         if abs(tank['x'] - MY_X) < so_close_x:
                                    #             so_close_x = abs(tank['x'] - MY_X)
                                    #             so_close_x_tmp = tank['x']
                                    #         if abs(tank['y'] - MY_Y) < so_close_y:
                                    #             so_close_y = abs(tank['y'] - MY_Y)
                                    #             so_close_y_tmp = tank['y']
                                    # for tank in tanks:
                                    #     if tank['id'] != MY_TANK_ID:
                                    #         if tank['x'] == so_close_x_tmp and tank['y'] == so_close_y_tmp:
                                    #             so_close_tank_id = tank['id']
                                    #         else:
                                    #             so_close_tank_id = ''


                                    my_direction = ''
                                    for tank in tanks:
                                        if tank['id'] == MY_TANK_ID:
                                            my_direction = tank['direction']

                                    for tank in tanks:
                                        if tank['id'] != MY_TANK_ID:

                                            if tank['y'] >= MY_Y and tank['y'] <= MY_Y + 35:
                                                if tank['direction'] == 'DOWN' and my_direction == 'UP':
                                                    client.fire_bullet(client.token)
                                                    client.turn_tank(client.token, 'RIGHT')
                                                if tank['direction'] == 'UP' and my_direction == 'DOWN':
                                                    client.fire_bullet(client.token)
                                                    client.turn_tank(client.token, 'LEFT')
                                            if tank['x'] >= MY_X and tank['x'] <= MY_X + 35:
                                                if tank['direction'] == 'LEFT' and my_direction == 'RIGHT':
                                                    client.fire_bullet(client.token)
                                                    client.turn_tank(client.token, 'UP')
                                                if tank['direction'] == 'RIGHT' and my_direction == 'LEFT':
                                                    client.fire_bullet(client.token)
                                                    client.turn_tank(client.token, 'DOWN')



                                    # print(so_close_x)
                                    # print(so_close_y)
                                    # print(so_close_tank_id)


                                    # distance = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
                                    #
                                    # itmp = 0
                                    # for tank in tanks:
                                    #     if tank['id'] != MY_TANK_ID:
                                    #         distance[itmp].append(tank['id'])
                                    #         distance[itmp].append( ((tank['x'] - MY_X)**2 + (tank['y'] - MY_Y)**2)**0.5)
                                    #     itmp += 1
                                    #
                                    # print(distance)






                                    if los:
                                        loserr()
                                    if won:
                                        winerr()

                                    pygame.display.flip()

                                client.connection.close()
                                # pygame.quit()


                            client = TankRpcClient()
                            client.check_server_status()
                            which_room = 'room-' + str(WHICH_ROOM)
                            client.obtain_token(which_room)
                            event_client = TankConsumerClient(which_room)
                            event_client.start()
                            client.turn_tank(client.token, 'UP')
                            game_start()

                            runtmp = True
                            while runtmp:

                                screen.fill((0, 0, 0))
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        runtmp = False
                                    if event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_r:
                                            runtmp = False

                                pygame.draw.rect(screen, (0, 0, 0), ((0, 0), (1000, 600)))
                                text = font.render('Игра закончена!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 40)
                                screen.blit(text, textRect)

                                text = font.render('Ваш итоговый счет: {}'.format(MY_SCORE), True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 150)
                                screen.blit(text, textRect)

                                text = font.render('Нажмите R чтобы сыграть заново!', True, (255, 255, 255))
                                textRect = text.get_rect()
                                textRect.center = (400, 350)
                                screen.blit(text, textRect)

                                pygame.display.flip()

                            #run = False
                        #print(room.func)




        SCREEN_W = 800
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        for room in rooms:
            room.draw(screen)


        pygame.display.flip()