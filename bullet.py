import pygame
import random
from enum import Enum
from tank import Tank
from direction import Direction
pygame.init()
pygame.mixer.init()

sound_shoot = pygame.mixer.Sound('sound_shoot.wav')





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




