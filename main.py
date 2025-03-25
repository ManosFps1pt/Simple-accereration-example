import pygame
from sympy.physics.units import acceleration

v2 = pygame.Vector2
pygame.init()

SCREEN = pygame.display.set_mode((800, 600))
rect = pygame.Rect(0, 300, 40, 20)
clock = pygame.time.Clock()
ACCELERATION = .1
FRICTION = .005
rect_acceleration: v2 = v2(0, 0)
rect_velocity: v2 = v2(0, 0)
rect_position: v2 = v2(0, 0)
BASE_FPS = 60

run = True
while run:
    fps = clock.get_fps()
    try:
        delta_time = BASE_FPS / fps
    except ZeroDivisionError:
        delta_time = 1 / BASE_FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    rect_acceleration = v2(0, 0)
    keys: tuple[bool] = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        rect_acceleration.y = - ACCELERATION * delta_time
    if keys[pygame.K_DOWN]:
        rect_acceleration.y = ACCELERATION * delta_time
    if keys[pygame.K_LEFT]:
        rect_acceleration.x = - ACCELERATION * delta_time
    if keys[pygame.K_RIGHT]:
       rect_acceleration.x = ACCELERATION * delta_time
    i = rect_velocity * FRICTION
    print(i)
    acceleration -= i
    rect_velocity += rect_acceleration
    rect_position += rect_velocity + .5 * rect_acceleration
    SCREEN.fill("#000000")
    rect.topleft = rect_position
    pygame.draw.rect(SCREEN, "#FFFFFF", rect)
    pygame.display.update()
    clock.tick(60)
pygame.quit()
