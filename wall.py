import pygame
import random
from enum import Enum
from tank import Tank
from direction import Direction
pygame.init()
pygame.mixer.init()

wall_sprite = pygame.image.load("wall_sprite.png")#.convert()
wall_sprite.set_colorkey((255, 255, 255))

class Wall:

    def __init__(self, x, y):
        self.size = 40 # in px
        self.x = x
        self.y = y

        self.sprite = wall_sprite
        self.sprite = pygame.transform.scale(self.sprite, (self.size, self.size))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))