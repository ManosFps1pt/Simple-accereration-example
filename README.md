# Acceleration and Friction Simulation in Pygame

This project demonstrates acceleration, velocity, and friction in a simple Pygame simulation. The object moves based on user input, applying acceleration in the direction of movement while gradually slowing down due to friction.

## Features
- Real-time movement simulation with acceleration and friction
- Delta time (`loop_time`) implementation for smooth and frame-rate independent physics
- Velocity capping to prevent excessive speed
- Boundary collision handling

## Controls
- **Arrow Keys**: Move the rectangle in the respective direction
- **Quit**: Close the window to exit the program

## Installation
Ensure you have Python and Pygame installed. If not, install Pygame using:
```sh
pip install pygame
```

## Running the Project
Run the Python script with:
```sh
python with_acceleration.py
```

## Physics Implementation
- **Velocity (`px/s`)**: Updated based on acceleration and friction.
- **Acceleration (`px/s²`)**: Applied when arrow keys are pressed.
- **Friction (`s⁻¹`)**: Reduces velocity over time.
- **Delta Time (`s`)**: Used for frame-rate independent calculations.

## Future Improvements
- Implement real-world unit scaling (e.g., meters instead of pixels)
- Add graphical indicators for velocity and acceleration
- Implement an interactive UI for physics adjustments

## License
This project is open-source under the MIT License.

---
**Author:** Emmanouil Dragasakis 
**Date:** 2025-03-27

