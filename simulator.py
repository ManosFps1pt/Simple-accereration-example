from pygame import Vector2
from pygame import math
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
WINDOW_SIZE = 1500
FIELD_PIXELS = 600
MARGIN = (WINDOW_SIZE - FIELD_PIXELS) // 2

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
    pixel_x = MARGIN + (x / FIELD_SIZE_INCHES) * FIELD_PIXELS
    pixel_y = MARGIN + ((FIELD_SIZE_INCHES - y) / FIELD_SIZE_INCHES) * FIELD_PIXELS
    return pygame.Vector2(pixel_x, pixel_y)

def pixel_to_ftc(px, py):
    """Convert Pygame screen coordinates to Cartesian FTC coordinates."""
    px_no_margin = px - MARGIN
    py_no_margin = py - MARGIN
    x = (px_no_margin / FIELD_PIXELS) * FIELD_SIZE_INCHES
    y = FIELD_SIZE_INCHES - (py_no_margin / FIELD_PIXELS) * FIELD_SIZE_INCHES
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
        
        self.moving_shot_lead_factor = 0.01
        self.virtual_aim_point = pygame.Vector2(0, 0)
        
    def look_to_goal(self, robot_pose, goal_pose, robot_heading=0):
        # Cartesian calculation
        dx = goal_pose.x - robot_pose.x
        dy = goal_pose.y - robot_pose.y
        atan2_ang = math.atan2(dy, dx)
        rad = atan2_ang - robot_heading
        self.angle_to_goal = normalize_angle(rad)

    def look_to_goal_while_moving(self, robot_pose, robot_velocity, goal_pose, robot_heading=0):
        # 1. Prevent crash if velocity is zero when getting angle
        vel_angle = 0.0
        if robot_velocity.length_squared() > 0.0001:
            vel_angle = robot_velocity.angle_to(pygame.Vector2(1, 0))
            # print(f"Velocity Angle: {vel_angle:.2f}")

        # 2. Get distance to goal
        distance = math.hypot(goal_pose.x - robot_pose.x, goal_pose.y - robot_pose.y)
        # 3. Apply Compensated pose (Note: robot_velocity.x ALREADY contains magnitude & direction)
        comp_x = robot_pose.x + self.moving_shot_lead_factor * robot_velocity.x * distance
        comp_y = robot_pose.y + self.moving_shot_lead_factor * robot_velocity.y * distance
        # comp_x = robot_pose.x + self.moving_shot_lead_factor * 100 * robot_velocity.x
        # comp_y = robot_pose.y + self.moving_shot_lead_factor * 100 *  robot_velocity.y
        compensated_pose = pygame.Vector2(comp_x, comp_y)
        
        # print(f"comp x ({comp_x}) = {self.moving_shot_lead_factor} * {robot_velocity.x} * {distance}")
        # 4. CRITICAL: Actually update the turret target angle (this was deleted)
        self.look_to_goal(compensated_pose, goal_pose, robot_heading)
        
        # 5. Save the exact virtual point for visualization.
        #    By deriving it dynamically from compensated_pose, the visuals will faithfully 
        #    draw no matter what math you plug into comp_x and comp_y above!
        lead_offset_x = compensated_pose.x - robot_pose.x
        lead_offset_y = compensated_pose.y - robot_pose.y
        
        self.virtual_aim_point = pygame.Vector2(
            goal_pose.x - lead_offset_x,
            goal_pose.y - lead_offset_y
        )
        
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
        pygame.draw.circle(screen, COLOR_PROJECTILE, (int(px), int(py)), int(self.radius_inches / FIELD_SIZE_INCHES * FIELD_PIXELS))

class Robot:
    def __init__(self):
        self.position = pygame.Vector2(72, 72) # Center of field
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        
        self.max_accel = 150.0 # inches/s^2
        self.friction = 3.0 # damping factor
        self.max_velocity = 40.0 # inches/s
        
        self.heading = 0.0 # radians
        self.angular_velocity = 0.0 # rad/s
        self.angular_accel = 50.0 # rad/s^2 (manual input)
        self.max_angular_accel = 50.0 # rad/s^2 (total)
        self.max_angular_vel = 16.0 # rad/s
        self.angular_friction = 10.0 # damping factor
        
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
            
        # 1b. Input for rotation
        self.angular_acceleration = 0.0
        if keys[pygame.K_q]:
            self.angular_acceleration += self.angular_accel
        if keys[pygame.K_e]:
            self.angular_acceleration -= self.angular_accel
            
        if joystick:
            # Handle standard controller right stick or triggers
            # Axis 2 is often right stick X or triggers on some controllers
            for axis in range(2, min(joystick.get_numaxes(), 4)):
                val = joystick.get_axis(axis)
                if abs(val) > 0.1:
                    self.angular_acceleration -= val * self.angular_accel
                    break
            
        # 2. Physics step
        self.acceleration -= self.velocity * self.friction
        self.velocity += self.acceleration * dt
        if self.velocity.length() > self.max_velocity:
            self.velocity.scale_to_length(self.max_velocity)
            
        self.position += self.velocity * dt + 0.5 * self.acceleration * (dt ** 2)
        
        # 2b. Rotational Physics step
        self.angular_acceleration -= self.angular_velocity * self.angular_friction
        self.angular_velocity += self.angular_acceleration * dt
        if abs(self.angular_velocity) > self.max_angular_vel:
            self.angular_velocity = math.copysign(self.max_angular_vel, self.angular_velocity)
            
        self.heading = normalize_angle(self.heading + self.angular_velocity * dt)
        
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
        self.turret.look_to_goal_while_moving(self.position, self.velocity, goal, self.heading)
        self.turret.update(dt)
    def draw(self, screen):
        # Draw Robot Base (Rotated)
        px, py = ftc_to_pixel(self.position.x, self.position.y)
        rect_w = (ROBOT_WIDTH_INCHES / FIELD_SIZE_INCHES) * FIELD_PIXELS
        rect_h = (ROBOT_HEIGHT_INCHES / FIELD_SIZE_INCHES) * FIELD_PIXELS
        
        # Calculate corners
        cos_h = math.cos(self.heading)
        sin_h = math.sin(self.heading)
        
        half_w = rect_w / 2
        half_h = rect_h / 2
        
        corners = [
            pygame.Vector2(half_w, half_h),
            pygame.Vector2(-half_w, half_h),
            pygame.Vector2(-half_w, -half_h),
            pygame.Vector2(half_w, -half_h)
        ]
        
        rotated_corners = []
        for c in corners:
            # Rotate corner (Y is inverted in Pygame screen coords vs math)
            # Math: x' = x*cos - y*sin, y' = x*sin + y*cos
            # But screen Y is down, so we adjust
            rx = c.x * cos_h + c.y * sin_h
            ry = - (c.x * sin_h - c.y * cos_h)
            rotated_corners.append((px + rx, py + ry))
            
        pygame.draw.polygon(screen, COLOR_ROBOT, rotated_corners)
        
        # Draw "Front" Indicator
        front_x = px + cos_h * (half_w * 0.8)
        front_y = py - sin_h * (half_w * 0.8)
        pygame.draw.circle(screen, (50, 50, 50), (int(front_x), int(front_y)), 4)
        
        # Draw Turret
        turret_length = max(rect_w, rect_h) * 0.6
        # math angle to screen coordinates:
        # absolute turret angle
        abs_turret_angle = self.heading + self.turret.angle
        end_px = px + math.cos(abs_turret_angle) * turret_length
        end_py = py - math.sin(abs_turret_angle) * turret_length 
        
        pygame.draw.line(screen, COLOR_TURRET, (px, py), (end_px, end_py), 5)
        # Draw a small circle at the base
        pygame.draw.circle(screen, COLOR_TURRET, (int(px), int(py)), 8)
        
        # --- Visualizing Vectors and Aiming ---
        
        # 1. Exact Point the Turret Aims (Virtual Aim Point)
        aim_px, aim_py = ftc_to_pixel(self.turret.virtual_aim_point.x, self.turret.virtual_aim_point.y)
        pygame.draw.circle(screen, (50, 255, 255), (int(aim_px), int(aim_py)), 4)
        cross_size = 10
        pygame.draw.line(screen, (50, 255, 255), (aim_px - cross_size, aim_py), (aim_px + cross_size, aim_py), 2)
        pygame.draw.line(screen, (50, 255, 255), (aim_px, aim_py - cross_size), (aim_px, aim_py + cross_size), 2)
        
        # 2. Intended Aim Line (from robot to virtual aim point)
        pygame.draw.line(screen, (0, 150, 150), (px, py), (aim_px, aim_py), 1)

        # 3. Laser Beam for Current Turret Line of Sight
        laser_end_px = px + math.cos(abs_turret_angle) * 2000
        laser_end_py = py - math.sin(abs_turret_angle) * 2000
        pygame.draw.line(screen, (255, 100, 100), (px, py), (laser_end_px, laser_end_py), 1)
        
        # 4. Robot Velocity Vector (Green)
        vel_scale = 0.5 # Scale down for visualization
        v_px, v_py = ftc_to_pixel(self.position.x + self.velocity.x * vel_scale, self.position.y + self.velocity.y * vel_scale)
        if self.velocity.length() > 1.0:
            pygame.draw.line(screen, (0, 255, 0), (px, py), (v_px, v_py), 3)
            pygame.draw.circle(screen, (0, 200, 0), (int(v_px), int(v_py)), 4)
            
        # 5. Robot Acceleration Vector (Orange)
        accel_scale = 0.2
        a_px, a_py = ftc_to_pixel(self.position.x + self.acceleration.x * accel_scale, self.position.y + self.acceleration.y * accel_scale)
        if self.acceleration.length() > 5.0:
            pygame.draw.line(screen, (255, 165, 0), (px, py), (a_px, a_py), 2)
            pygame.draw.circle(screen, (200, 100, 0), (int(a_px), int(a_py)), 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("FTC Turret Simulator")
    clock = pygame.time.Clock()
    
    # Load Field Background
    field_image = None
    field_path = resource_path("field.png")
    if os.path.exists(field_path):
        try:
            raw_field = pygame.image.load(field_path).convert()
            field_image = pygame.transform.scale(raw_field, (FIELD_PIXELS, FIELD_PIXELS))
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
                    projectiles.append(Projectile(robot.position, robot.heading + robot.turret.angle, projectile_speed, robot.velocity))
                elif event.key == pygame.K_TAB:
                    # Switch Targets
                    robot.is_targeting_red = not robot.is_targeting_red
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # A Button
                    projectiles.append(Projectile(robot.position, robot.heading + robot.turret.angle, projectile_speed, robot.velocity))
                elif event.button == 1: # B Button
                    robot.is_targeting_red = not robot.is_targeting_red

        is_shooting = keys[pygame.K_SPACE] or (joystick and joystick.get_button(0))
        if is_shooting:
            space_held_time += dt
            rapid_fire_timer -= dt
            if space_held_time > 0.4 and rapid_fire_timer <= 0:
                projectiles.append(Projectile(robot.position, robot.heading + robot.turret.angle, projectile_speed, robot.velocity))
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
        screen.fill(COLOR_BG)
        if field_image:
            screen.blit(field_image, (MARGIN, MARGIN))
            
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
            f"Pose: ({robot.position.x:.1f}, {robot.position.y:.1f}) @ {math.degrees(robot.heading):.0f} deg",
            f"Vel: ({robot.velocity.x:.1f}, {robot.velocity.y:.1f})",
            f"Targeting: {goal_str} [Press TAB to switch]",
            f"Turret Ang: {math.degrees(robot.turret.angle):.0f} deg (Rel) (Target: {math.degrees(robot.turret.angle_to_goal):.0f})",
            f"Controls: Arrows = Move, Q/E = Rotate, SPACE = Shoot",
            f"Vectors: Green=Vel, Orange=Accel, Cyan=Aim, Red=Laser"
        ]
        
        for i, text in enumerate(telems):
            surf = font.render(text, True, (128, 255, 0))
            screen.blit(surf, (10, 10 + i * 25))

        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
