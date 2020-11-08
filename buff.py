import pygame
import random
from enum import Enum
from tank import Tank
from direction import Direction
pygame.init()
pygame.mixer.init()

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