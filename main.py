import pygame
import random
from enum import Enum
from tank import Tank
from direction import Direction
from bullet import Bullet
from wall import Wall
from buff import Buff

pygame.init()
pygame.mixer.init()

size_w = 800
size_h = 600
screen = pygame.display.set_mode((size_w, size_h))
background = pygame.image.load("background.jpg").convert()
background = pygame.transform.scale(background, (size_w, size_h))
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





run = True
tank_1 = Tank(300, 300, 200, tank1_sprite, bullet1_sprite)
tank_2 = Tank(100, 100, 200, tank2_sprite, bullet2_sprite, pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_SPACE)

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

#tank1_sprite = pygame.transform.rotate(tank1_sprite, 270)

wallprob = Wall(1000,1000)
walls = []

for i in range(0, size_h, wallprob.size):
    for j in range(0, size_w, wallprob.size):
        rand = random.randint(1,100)
        if rand <= 10:
            walls.append(Wall(j, i))


buffs = []
buff_time = 0
buff_time_when = random.randint(1, 10)

while run:
    millis = clock.tick(FPS)
    seconds = millis / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False

            for tank in tanks:
                if event.key in tank.KEY.keys():
                    tank.change_direction(tank.KEY[event.key])
                if event.key == tank.fire_key:
                    if tank.recharge != True:
                        if tank.buff == False:
                            bullets.append(Bullet(tank,500, screen))
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

            if ( ( (tank.x <= x2 and tank.x >= x1) or (tank.x + tank.width <= x2 and tank.x + tank.width >= x1) ) and (tank.y <= y2 and tank.y >= y1)) or (((tank.x <= x2 and tank.x >= x1) or (tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (tank.y + tank.width <= y2 and tank.y + tank.width >= y1)) :
                tank.lifes -= 1
                del walls[i]
            i += 1

        i = 0
        for buff in buffs:
            x1 = buff.x
            y1 = buff.y
            x2 = buff.x + buff.size
            y2 = buff.y + buff.size

            if ( ( (tank.x <= x2 and tank.x >= x1) or (tank.x + tank.width <= x2 and tank.x + tank.width >= x1) ) and (tank.y <= y2 and tank.y >= y1)) or (((tank.x <= x2 and tank.x >= x1) or (tank.x + tank.width <= x2 and tank.x + tank.width >= x1)) and (tank.y + tank.width <= y2 and tank.y + tank.width >= y1)):
                tank.buff = True
                del buffs[i]




        tank.move(seconds)
        tank.draw(screen, size_w, size_h)





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
            if (((bullet.x <= x2 and bullet.x >= x1) or (bullet.x + bullet.bullet_h <= x2 and bullet.x + bullet.bullet_h >= x1)) and (
                    bullet.y <= y2 and bullet.y >= y1)) or (
                    ((bullet.x <= x2 and bullet.x >= x1) or (bullet.x + bullet.bullet_h <= x2 and bullet.x + bullet.bullet_h >= x1)) and (
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
            buff_x = random.randint(0, size_w / wallprob.size)
            buff_y = random.randint(0, size_h / wallprob.size)
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
    #wall.draw(screen)
    ################



    #print(seconds)
    pygame.display.flip()

pygame.quit()
