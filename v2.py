import pygame
from pygame import Vector2

v2 = pygame.Vector2
pygame.init()

SCREEN_SIZE = v2(800, 600)
SCREEN = pygame.display.set_mode(SCREEN_SIZE)
rect = pygame.Rect(0, 300, 40, 20)
clock = pygame.time.Clock()
ACCELERATION = 5000 # px/s²?
FRICTION = 10 # s¯¹
MAX_VELOCITY = 500 # px/s
rect_acceleration = v2(0, 0) # px/s²?
rect_velocity = v2(0, 0) # px/s
rect_position: Vector2 = v2(0, 300) # px
BASE_FPS = 0

run = True
while run:
    loop_time = clock.tick(BASE_FPS) / 1000  # Convert ms to seconds
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Reset acceleration
    rect_acceleration = v2(0, 0)
    if abs(rect_velocity.x) < .001:
        rect_velocity.x = 0
    if abs(rect_velocity.y) < .001:
        rect_velocity.y = 0

    # Key press detection
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        rect_acceleration.y -= ACCELERATION
    if keys[pygame.K_DOWN]:
        rect_acceleration.y += ACCELERATION
    if keys[pygame.K_LEFT]:
        rect_acceleration.x -= ACCELERATION
    if keys[pygame.K_RIGHT]:
        rect_acceleration.x += ACCELERATION

    # Apply acceleration
    if rect_acceleration.length() > 0:
        rect_acceleration.scale_to_length(ACCELERATION)

    # Apply friction
    rect_acceleration -= rect_velocity * FRICTION

    # Update velocity with delta time
    rect_velocity += rect_acceleration * loop_time

    # Cap velocity
    if rect_velocity.length() > MAX_VELOCITY:
        rect_velocity.scale_to_length(MAX_VELOCITY)

    # Update position with delta time
    rect_position += rect_velocity * loop_time + 0.5 * rect_acceleration * (loop_time ** 2)

    # Screen boundaries
    if rect_position.x<1:
        rect_position.x=1
        rect_velocity.x = 0
    if rect_position.y<1:
        rect_position.y=1
        rect_velocity.y = 0
    if rect_position.x > SCREEN_SIZE.x - rect.width + 1:
        rect_position.x = SCREEN_SIZE.x - rect.width + 1
        rect_velocity.x = 0
    if rect_position. y > SCREEN_SIZE.y - rect.height + 1:
        rect_position.y = SCREEN_SIZE.y - rect.height + 1
        rect_velocity.y = 0
    fps = clock.get_fps()
    if fps == 0:
        continue
    output_msg = f"{clock.get_fps():.2f} fps\t"\
                 f"acceleration: {rect_acceleration} px/s², "\
                 f"velocity: {rect_velocity} px/s, "\
                 f"vector length: {rect_velocity.length():.2f} px/s"
    pygame.display.set_caption(output_msg)
    print(output_msg)
    # Draw updates
    SCREEN.fill("#000000")
    rect.topleft = rect_position
    pygame.draw.rect(SCREEN, "#FFFFFF", rect)
    pygame.display.update()

pygame.quit()
