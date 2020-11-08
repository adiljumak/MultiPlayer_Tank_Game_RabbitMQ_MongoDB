import pygame

pygame.init()


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
