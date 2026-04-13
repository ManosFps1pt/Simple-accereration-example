# FTC Turret & Acceleration Simulator

This project simulates complex physical robot behaviors combined with high-level FTC (FIRST Tech Challenge) targeting logic in a 2D Pygame environment. It evolved from a simple block-acceleration example into a fully-fledged top-down robotic simulator, complete with Gamepad support, dynamic turret logic, and projectile mechanics.

## Features

- **Realistic Chassis Physics:** Smooth, delta-time-dependent robot acceleration and friction that automatically caps at a maximum velocity.
- **Trapezoidal Motion Profiling:** The turret doesn't just snap to its target; it respects physical constraints by accelerating linearly to a maximum rotational speed, then decelerating accurately to "lock" onto the target angle.
- **Lead Factor Compensation:** When the robot is driving at high speeds, the targeting algorithm leads the goal based on the robot's existing momentum vectors to ensure projectiles hit accurately while moving.
- **Gamepad Support:** Drive the robot seamlessly with your controller's left thumbstick and map shots/targets to your controller buttons automatically. 
- **Rapid Fire:** Hold down the fire button for 0.4s to automatically unleash projectiles.

## Controls

### Keyboard
- **Arrow Keys:** Drive the robot in the respective directions.
- **Spacebar:** Tap to shoot a projectile, or hold it down for full-auto rapid fire.
- **Tab Key:** Swap the turret's targeting priority between the Red Goal `(144, 144)` and the Blue Goal `(0, 144)`.

### Gamepad (Optional)
- **Left Thumbstick:** Analog drive for smooth acceleration control.
- **A Button (Button 0):** Shoot projectiles / Rapid fire.
- **B Button (Button 1):** Swap target priorities.

## Installation

Ensure you have Python and Pygame installed. To install Pygame:
```sh
pip install pygame
```

## Running the Simulator

### Option 1: Run via Python
Execute the source script directly:
```sh
python simulator.py
```
*(Ensure `field.png` is in the same directory as the script!)*

### Option 2: Run the Executable
This project includes a bundled, portable `.exe` file. PyInstaller compiles `simulator.py` into a single standalone application.
1. Navigate to the `dist/` directory.
2. Double click `simulator.exe`.
*Note: The `field.png` background is physically injected into the .exe format, meaning you can drop this executable anywhere (Desktop, flash drives, etc.) without losing the background!*

## Building the Executable Yourself
To create the `.exe` file manually, ensure you have PyInstaller installed (`pip install pyinstaller`), then run:
```sh
python -m PyInstaller --onefile --noconsole --add-data "field.png;." simulator.py
```

## Physics Implementation
- Coordinate Space: Translates an FTC standard `144x144` coordinate dimension to an `800x800` pixel mapping dynamically. 
- Uses mathematical `atan2` principles equivalent to the real-world java system.

## License
This project is open-source under the MIT License.

---
**Author:** Emmanouil Dragasakis 
**Date:** 2026-04-13
