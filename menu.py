import pygame
import os
from button import Button

pygame.init()

WHICH_ROOM = 1

size_w = 800
size_h = 600

screen = pygame.display.set_mode((size_w, size_h))
menu_background = pygame.image.load("menu_background.png").convert()
menu_background = pygame.transform.scale(menu_background, (size_w, size_h))


run = True

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
        os.startfile('main.py')
        run = False
    else:
        pos = pygame.mouse.get_pos()
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for room in rooms:
                    if room.x - 50 <= pos[0] <= room.x + 50 and room.y - 20 <= pos[1] <= room.y + 20:
                        WHICH_ROOM = room.func
                        run = False
                        if MULTI_PLAY:
                            os.startfile('multi_main.py')
                            run = False
                        if MULTI_AI_PLAY:
                            print("OK")
                            run = False
                        #print(room.func)





        for room in rooms:
            room.draw(screen)


        pygame.display.flip()