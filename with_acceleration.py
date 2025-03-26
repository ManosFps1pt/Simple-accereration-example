import pygame

v2 = pygame.Vector2
pygame.init()

SCREEN_SIZE = v2(800, 600)
SCREEN = pygame.display.set_mode(SCREEN_SIZE)
rect = pygame.Rect(0, 300, 40, 20)
clock = pygame.time.Clock()
ACCELERATION = .05
FRICTION = .1
MAX_VELOCITY = 5
rect_acceleration: v2 = v2(0, 0)
rect_velocity: v2 = v2(0, 0)
rect_position: v2 = v2(0, 0)
BASE_FPS = 0

run = True
while run:
    loop_time: int = clock.tick(BASE_FPS) # ms
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    if abs(rect_velocity.x) < .001:
        rect_velocity.x = 0
    if abs(rect_velocity.y) < .001:
        rect_velocity.y = 0
    rect_acceleration = v2(0, 0)
    keys: tuple[bool] = pygame.key.get_pressed()
    acceleration_length = ACCELERATION * loop_time
    if acceleration_length == 0:
        continue
    if keys[pygame.K_UP]:
        rect_acceleration.y -= acceleration_length
    if keys[pygame.K_DOWN]:
        rect_acceleration.y += acceleration_length
    if keys[pygame.K_LEFT]:
        rect_acceleration.x -= acceleration_length
    if keys[pygame.K_RIGHT]:
       rect_acceleration.x += acceleration_length
    if rect_acceleration != v2(0, 0):
        rect_acceleration.scale_to_length(acceleration_length)
    rect_acceleration -= rect_velocity * FRICTION
    rect_velocity += rect_acceleration
    if rect_velocity != v2(0, 0) and rect_velocity.length() > MAX_VELOCITY:
        rect_velocity.scale_to_length(MAX_VELOCITY)

    pygame.display.set_caption(f"{clock.get_fps():.2f} fps \t velocity: {rect_velocity}")
    rect_position += rect_velocity + .5 * rect_acceleration
    if rect_position.x<0:
        rect_position.x=1
    if rect_position.y<0:
        rect_position.y=1
    if rect_position.x > SCREEN_SIZE.x - rect.width + 1:
        rect_position.x = SCREEN_SIZE.x - rect.width + 1
    if rect_position. y >SCREEN_SIZE.y - rect.height + 1:
        rect_position.y = SCREEN_SIZE.y - rect.height + 1
    SCREEN.fill("#000000")
    rect.topleft = rect_position
    pygame.draw.rect(SCREEN, "#FFFFFF", rect)
    pygame.display.update()

pygame.quit()
