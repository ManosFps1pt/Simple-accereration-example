import pygame
import math
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Configuration ---
SCREEN_SIZE = 800
FIELD_SIZE_INCHES = 144.0
ROBOT_WIDTH_INCHES = 18.0
ROBOT_HEIGHT_INCHES = 18.0

# Colors
COLOR_BG = (30, 30, 30)
COLOR_ROBOT = (200, 200, 200)
COLOR_TURRET = (255, 50, 50)
COLOR_RED_GOAL = (255, 0, 0)
COLOR_BLUE_GOAL = (0, 0, 255)
COLOR_PROJECTILE = (255, 255, 0)

# Target Goals (Cartesian)
RED_GOAL_POSE = pygame.Vector2(144, 144)
BLUE_GOAL_POSE = pygame.Vector2(0, 144)

# --- Coordinate Helpers ---
def ftc_to_pixel(x, y):
    """Convert Cartesian FTC coordinates (0-144) to Pygame screen coordinates."""
    pixel_x = (x / FIELD_SIZE_INCHES) * SCREEN_SIZE
    pixel_y = ((FIELD_SIZE_INCHES - y) / FIELD_SIZE_INCHES) * SCREEN_SIZE
    return pygame.Vector2(pixel_x, pixel_y)

def pixel_to_ftc(px, py):
    """Convert Pygame screen coordinates to Cartesian FTC coordinates."""
    x = (px / SCREEN_SIZE) * FIELD_SIZE_INCHES
    y = FIELD_SIZE_INCHES - (py / SCREEN_SIZE) * FIELD_SIZE_INCHES
    return pygame.Vector2(x, y)

def normalize_angle(angle):
    """Normalize angle to be between -pi and pi."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle

# --- Classes ---
class Turret:
    def __init__(self):
        self.angle = 0.0 # radians
        self.velocity = 0.0 # rad/s
        self.max_velocity = 8.0 # rad/s
        self.acceleration = 150.0 # rad/s^2
        self.angle_to_goal = 0.0
        
        self.moving_shot_lead_factor = 1.0
        
    def look_to_goal(self, robot_pose, goal_pose, robot_heading=0):
        # Cartesian calculation
        dx = goal_pose.x - robot_pose.x
        dy = goal_pose.y - robot_pose.y
        atan2_ang = math.atan2(dy, dx)
        rad = atan2_ang - robot_heading
        self.angle_to_goal = normalize_angle(rad)

    def look_to_goal_while_moving(self, robot_pose, robot_velocity, goal_pose, is_red=True):
        # Compensated pose based on lead factor
        comp_x = robot_pose.x + self.moving_shot_lead_factor * robot_velocity.x
        comp_y = robot_pose.y + self.moving_shot_lead_factor * robot_velocity.y
        compensated_pose = pygame.Vector2(comp_x, comp_y)
        self.look_to_goal(robot_pose, compensated_pose) # Target the compensated pose from the robot's current pose! 
        # Wait, the java code does: lookToGoal(compensatedPose, isRed). 
        # Aiming AT (goal + a*vel) from (pose) is equivalent to aiming AT (goal) from (pose - a*vel).
        # So we should calculate angle from compensated_pose TO goal_pose.
        self.look_to_goal(compensated_pose, goal_pose, 0)
        
    def update(self, dt):
        """Light Trapezoidal Motion Profile"""
        distance = normalize_angle(self.angle_to_goal - self.angle)
        
        # Calculate stopping distance: d = v^2 / (2a)
        stopping_distance = (self.velocity ** 2) / (2.0 * self.acceleration)
        
        target_velocity = 0.0
        if abs(distance) > stopping_distance + 0.05: # Add a tiny margin
            target_velocity = math.copysign(self.max_velocity, distance)
            
        # Move current velocity towards target velocity
        if self.velocity < target_velocity:
            self.velocity = min(self.velocity + self.acceleration * dt, target_velocity)
        elif self.velocity > target_velocity:
            self.velocity = max(self.velocity - self.acceleration * dt, target_velocity)
            
        self.angle = normalize_angle(self.angle + self.velocity * dt)
        
        # Hard lock if we are very close and slow
        if abs(distance) < 0.02 and abs(self.velocity) < 0.1:
            self.angle = self.angle_to_goal
            self.velocity = 0

class Projectile:
    def __init__(self, position, angle, velocity_magnitude, initial_velocity):
        self.position = pygame.Vector2(position) # FTC coords
        self.velocity = pygame.Vector2(
            math.cos(angle) * velocity_magnitude,
            math.sin(angle) * velocity_magnitude
        ) + pygame.Vector2(initial_velocity)
        self.active = True
        self.radius_inches = 2.0

    def update(self, dt):
        self.position += self.velocity * dt
        if not (0 <= self.position.x <= FIELD_SIZE_INCHES and 0 <= self.position.y <= FIELD_SIZE_INCHES):
            self.active = False
            
    def draw(self, screen):
        px, py = ftc_to_pixel(self.position.x, self.position.y)
        pygame.draw.circle(screen, COLOR_PROJECTILE, (int(px), int(py)), int(self.radius_inches / FIELD_SIZE_INCHES * SCREEN_SIZE))

class Robot:
    def __init__(self):
        self.position = pygame.Vector2(72, 72) # Center of field
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        
        self.max_accel = 150.0 # inches/s^2
        self.friction = 3.0 # damping factor
        self.max_velocity = 40.0 # inches/s
        
        self.turret = Turret()
        self.is_targeting_red = True
    
    def update(self, dt, keys, joystick=None):
        # 1. Input for acceleration
        self.acceleration = pygame.Vector2(0, 0)
        if keys[pygame.K_UP]:
            self.acceleration.y += self.max_accel
        if keys[pygame.K_DOWN]:
            self.acceleration.y -= self.max_accel
        if keys[pygame.K_LEFT]:
            self.acceleration.x -= self.max_accel
        if keys[pygame.K_RIGHT]:
            self.acceleration.x += self.max_accel
            
        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            # Deadzone
            if abs(axis_x) > 0.1:
                self.acceleration.x += axis_x * self.max_accel
            if abs(axis_y) > 0.1:
                self.acceleration.y -= axis_y * self.max_accel # Y is typically inverted on thumbsticks
            
        if self.acceleration.length() > 0:
            self.acceleration.scale_to_length(self.max_accel)
            
        # 2. Physics step
        self.acceleration -= self.velocity * self.friction
        self.velocity += self.acceleration * dt
        if self.velocity.length() > self.max_velocity:
            self.velocity.scale_to_length(self.max_velocity)
            
        self.position += self.velocity * dt + 0.5 * self.acceleration * (dt ** 2)
        
        # 3. Boundaries (keep robot center inside field)
        half_w = ROBOT_WIDTH_INCHES / 2
        half_h = ROBOT_HEIGHT_INCHES / 2
        
        if self.position.x < half_w:
            self.position.x = half_w
            self.velocity.x = 0
        elif self.position.x > FIELD_SIZE_INCHES - half_w:
            self.position.x = FIELD_SIZE_INCHES - half_w
            self.velocity.x = 0
            
        if self.position.y < half_h:
            self.position.y = half_h
            self.velocity.y = 0
        elif self.position.y > FIELD_SIZE_INCHES - half_h:
            self.position.y = FIELD_SIZE_INCHES - half_h
            self.velocity.y = 0
            
        # 4. Turret Update
        goal = RED_GOAL_POSE if self.is_targeting_red else BLUE_GOAL_POSE
        self.turret.look_to_goal_while_moving(self.position, self.velocity, goal, self.is_targeting_red)
        self.turret.update(dt)

    def draw(self, screen):
        # Draw Robot Base
        px, py = ftc_to_pixel(self.position.x, self.position.y)
        rect_w = (ROBOT_WIDTH_INCHES / FIELD_SIZE_INCHES) * SCREEN_SIZE
        rect_h = (ROBOT_HEIGHT_INCHES / FIELD_SIZE_INCHES) * SCREEN_SIZE
        
        rect = pygame.Rect(0, 0, rect_w, rect_h)
        rect.center = (px, py)
        pygame.draw.rect(screen, COLOR_ROBOT, rect)
        
        # Draw Turret
        turret_length = max(rect_w, rect_h) * 0.6
        # math angle to screen coordinates:
        # positive dx -> right, positive dy -> UP!
        end_px = px + math.cos(self.turret.angle) * turret_length
        end_py = py - math.sin(self.turret.angle) * turret_length # minus because UP is -Y visually
        
        pygame.draw.line(screen, COLOR_TURRET, (px, py), (end_px, end_py), 5)
        # Draw a small circle at the base
        pygame.draw.circle(screen, COLOR_TURRET, (int(px), int(py)), 8)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pygame.display.set_caption("FTC Turret Simulator")
    clock = pygame.time.Clock()
    
    # Load Field Background
    field_image = None
    field_path = resource_path("field.png")
    if os.path.exists(field_path):
        try:
            raw_field = pygame.image.load(field_path).convert()
            field_image = pygame.transform.scale(raw_field, (SCREEN_SIZE, SCREEN_SIZE))
        except Exception as e:
            print(f"Warning: Could not load field.png: {e}")

    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()
    joystick = joysticks[0] if joysticks else None

    font = pygame.font.SysFont(None, 24)
    robot = Robot()
    projectiles = []
    
    projectile_speed = 100.0 # inches/s (FTC shots are fast)
    
    space_held_time = 0.0
    rapid_fire_timer = 0.0
    
    run = True
    while run:
        dt = clock.tick(60) / 1000.0
        if dt == 0:
            continue
            
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Shoot!
                    projectiles.append(Projectile(robot.position, robot.turret.angle, projectile_speed, robot.velocity))
                elif event.key == pygame.K_TAB:
                    # Switch Targets
                    robot.is_targeting_red = not robot.is_targeting_red
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # A Button
                    projectiles.append(Projectile(robot.position, robot.turret.angle, projectile_speed, robot.velocity))
                elif event.button == 1: # B Button
                    robot.is_targeting_red = not robot.is_targeting_red

        is_shooting = keys[pygame.K_SPACE] or (joystick and joystick.get_button(0))
        if is_shooting:
            space_held_time += dt
            rapid_fire_timer -= dt
            if space_held_time > 0.4 and rapid_fire_timer <= 0:
                projectiles.append(Projectile(robot.position, robot.turret.angle, projectile_speed, robot.velocity))
                rapid_fire_timer = 0.1 # shoot every 0.1 seconds
        else:
            space_held_time = 0.0
            rapid_fire_timer = 0.0

        # Logic
        robot.update(dt, keys, joystick)
        for p in projectiles:
            p.update(dt)
        projectiles = [p for p in projectiles if p.active]
            
        # Draw
        if field_image:
            screen.blit(field_image, (0, 0))
        else:
            screen.fill(COLOR_BG)
            
        # Draw Goals
        red_px, red_py = ftc_to_pixel(RED_GOAL_POSE.x, RED_GOAL_POSE.y)
        pygame.draw.circle(screen, COLOR_RED_GOAL, (int(red_px), int(red_py)), 10)
        
        blue_px, blue_py = ftc_to_pixel(BLUE_GOAL_POSE.x, BLUE_GOAL_POSE.y)
        pygame.draw.circle(screen, COLOR_BLUE_GOAL, (int(blue_px), int(blue_py)), 10)
        
        for p in projectiles:
            p.draw(screen)
            
        robot.draw(screen)
        
        # Telemetry
        goal_str = "RED (144, 144)" if robot.is_targeting_red else "BLUE (0, 144)"
        telems = [
            f"FPS: {clock.get_fps():.1f}",
            f"Pose: ({robot.position.x:.1f}, {robot.position.y:.1f})",
            f"Vel: ({robot.velocity.x:.1f}, {robot.velocity.y:.1f})",
            f"Targeting: {goal_str} [Press TAB to switch]",
            f"Turret Ang: {math.degrees(robot.turret.angle):.0f} deg (Target: {math.degrees(robot.turret.angle_to_goal):.0f})",
            f"Press SPACE to Shoot"
        ]
        
        for i, text in enumerate(telems):
            surf = font.render(text, True, (128, 255, 0))
            screen.blit(surf, (10, 10 + i * 25))

        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
