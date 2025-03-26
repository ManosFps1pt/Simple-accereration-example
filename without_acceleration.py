import pygame

v2 = pygame.Vector2
pygame.init()

SCREEN_SIZE = v2(800, 600)
SCREEN = pygame.display.set_mode(SCREEN_SIZE)
rect = pygame.Rect(0, 300, 40, 20)
clock = pygame.time.Clock()
MAX_VELOCITY = 5
rect_velocity: v2 = v2(0, 0)
rect_position: v2 = v2(0, 0)
BASE_FPS = 60

run = True
while run:
    loop_time: int = clock.tick(BASE_FPS) # ms
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    keys: tuple[bool] = pygame.key.get_pressed()
    rect_velocity = v2(0, 0)
    if keys[pygame.K_UP]:
        rect_velocity.y -= MAX_VELOCITY
    if keys[pygame.K_DOWN]:
        rect_velocity.y += MAX_VELOCITY
    if keys[pygame.K_LEFT]:
        rect_velocity.x -= MAX_VELOCITY
    if keys[pygame.K_RIGHT]:
        rect_velocity.x += MAX_VELOCITY
    print(rect_velocity)
    if rect_velocity != v2(0, 0) and rect_velocity.length() > MAX_VELOCITY:
        rect_velocity.scale_to_length(MAX_VELOCITY)
    rect_position += rect_velocity
    if rect_position.x<0: rect_position.x=1
    if rect_position.y<0: rect_position.y=1
    if rect_position.x>SCREEN_SIZE.x-41: rect_position.x=SCREEN_SIZE.x-41
    if rect_position.y>SCREEN_SIZE.y-21: rect_position.y=SCREEN_SIZE.y-21
    rect.topleft = rect_position
    pygame.display.set_caption(f"{clock.get_fps():.2f} fps \t velocity: {rect_velocity}")
    SCREEN.fill("#000000")
    rect.topleft = rect_position
    pygame.draw.rect(SCREEN, "#FFFFFF", rect)
    pygame.display.update()

pygame.quit()
