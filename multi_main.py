import pygame
import os
import random
from enum import Enum
from tank import Tank
from direction import Direction
from bullet import Bullet
from wall import Wall
from buff import Buff

#from menu import WHICH_ROOM


font = pygame.font.Font('freesansbold.ttf', 32)
font2 = pygame.font.Font('freesansbold.ttf', 15)

pygame.init()
SCREEN_W = 1000
SCREEN_H = 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))


background = pygame.image.load("background.jpg").convert()
background = pygame.transform.scale(background, (SCREEN_W - 200, SCREEN_H))
FPS = 60
clock = pygame.time.Clock()


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


my_bullet_sprite = pygame.image.load("bullet1_sprite.png").convert()
my_bullet_sprite = pygame.transform.scale(my_bullet_sprite, (15, 5))
my_bullet_sprite.set_colorkey((255, 255, 255))
my_bullet_sprite_UP = pygame.transform.rotate(my_bullet_sprite, 90)
my_bullet_sprite_LEFT = pygame.transform.rotate(my_bullet_sprite, 180)
my_bullet_sprite_DOWN = pygame.transform.rotate(my_bullet_sprite, 270)



bullet1_sprite = pygame.image.load("bullet2_sprite.png").convert()
bullet1_sprite = pygame.transform.scale(bullet1_sprite, (15, 5))
bullet1_sprite.set_colorkey((255, 255, 255))
bullet1_sprite_UP = pygame.transform.rotate(bullet1_sprite, 90)
bullet1_sprite_LEFT = pygame.transform.rotate(bullet1_sprite, 180)
bullet1_sprite_DOWN = pygame.transform.rotate(bullet1_sprite, 270)


import json
import uuid
from threading import Thread

import pika

import pygame





IP = '34.254.177.17'
PORT = '5672'
VIRTUAL_HOST = 'dar-tanks'
USERNAME = 'dar-tanks'
PASSWORD = '5orPLExUYnyVYZg48caMpX'
MY_TANK_ID = ''
MY_SCORE = ''

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

def draw_tank(x, y, width, height, direction, tank_id, tank_health):
    global MY_TANK_ID, font2, screen

    if tank_id == MY_TANK_ID:
        if direction == 'RIGHT':
            screen.blit(my_tank_sprite, (x, y))
            tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
            tank_id_textRect = tank_id_text.get_rect()
            tank_id_textRect.center = (x + 15, y + width + 10)
            screen.blit(tank_id_text, tank_id_textRect)
            for i in range(0, tank_health):
                r = int(((width / 3) / 2) - 2)
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2), r)

        if direction == 'LEFT':
            screen.blit(my_tank_sprite_LEFT, (x, y))
            tank_id_text = font2.render('{}'.format(tank_id), True, (255, 255, 255))
            tank_id_textRect = tank_id_text.get_rect()
            tank_id_textRect.center = (x + 15, y + width + 10)
            screen.blit(tank_id_text, tank_id_textRect)

            for i in range(0, tank_health):
                r = int(((width / 3) / 2) - 2)
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 4, y + r - 4), r)
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 3, y + r + width),
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 1, y + r - 4), r)
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r, y + r - 2), r)
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 4, y + r - 4), r)
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 3, y + r + width),
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
                pygame.draw.circle(screen, (0, 255, 0), (2 * r + x + i * 3 * r + 1, y + r - 4), r)
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
    while(max >= 0):


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
                    #print("")
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


                #txt_losers = ','.join(i['tankId'] for i in losers)
                #print(txt_losers)
                # if tank['id'] == MY_TANK_ID: #and tank['health'] == 0:
                #     for lose in losers:
                #
                #             print(','.join(lose['tankId']))

                #    print(tank['health'])
                #for lose in losers:
                    #print(lose['tankid'])
                #     lose(tank['score'])
                #print(losers)


                # txt_losers = ','.join(i['tankId'] for i in losers)
                # print(txt_losers)

                draw_tank(tank_x, tank_y, tank_width, tank_height, tank_direction, tank_id, tank_health)




            for bullet in bullets:
                bullet_x = bullet['x']
                bullet_y = bullet['y']
                bullet_owner = bullet['owner']
                bullet_width = bullet['width']
                bullet_height = bullet['height']
                bullet_direction = bullet['direction']
                draw_bullet(bullet_x, bullet_y, bullet_width, bullet_height, bullet_direction, bullet_owner) # if bullet_owner == my_tank_id
        except:
            pass



        if los:
            loserr()
        if won:
            winerr()

        pygame.display.flip()

    client.connection.close()
    #pygame.quit()

client = TankRpcClient()
client.check_server_status()
client.obtain_token('room-1')
event_client = TankConsumerClient('room-1')
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


os.startfile('menu.py')
pygame.quit()


       # client.turn_tank(client.token, 'UP')

