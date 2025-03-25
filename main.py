import pygame
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


run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    keys: tuple[bool] = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        rect_acceleration.y = - ACCELERATION # * delta_time
    if keys[pygame.K_DOWN]:
        rect_acceleration.y = ACCELERATION # * delta_time
    if keys[pygame.K_LEFT]:
        rect_acceleration.x = - ACCELERATION # * delta_time
    if keys[pygame.K_RIGHT]:
       rect_acceleration.x = ACCELERATION # * delta_time
    SCREEN.fill("#000000")
    pygame.draw.rect(SCREEN, "#FFFFFF", rect)
    pygame.display.update()
pygame.quit()
