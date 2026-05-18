# Position-Based Turret LUT Aiming

## Goal

Implement a **position-based virtual aim point LUT** for the FTC robot turret.

This system is meant to fix shots that miss when the robot shoots from awkward field angles.  
Instead of always aiming at the geometric center of the goal, the turret aims at a **different virtual point** that depends on the robot's field position.

## Core Idea

Normal aiming does this:

- robot pose -> compute angle to real goal center -> point turret there

The LUT system does this:

- robot pose -> look up calibrated virtual aim point -> compute angle to that point -> point turret there

So the LUT does **not** map distance to angle.
It maps:

- **robot field position** -> **virtual target point**

Each LUT sample is:

```python
((robot_x, robot_y), (aim_x, aim_y))
```

Example:

```python
((36.0, 108.0), (20.0, 141.0))
```

Meaning:

- if the robot is near `(36, 108)`
- the turret should aim toward `(20, 141)`
- not necessarily toward the real goal center

## Why This Works

Two robot positions can be the same distance from the goal but need different corrections.

The error usually depends on:

- approach angle
- lateral offset
- release geometry
- ball trajectory
- hood / shooter bias
- robot-specific mechanical effects

Because of that, a distance-only correction is not enough.
A field-position LUT is the correct model.

## Required Inputs

The robot code needs:

- robot field X
- robot field Y
- robot heading
- selected scoring target / goal

Field position should be in the same coordinate frame used to tune the LUT.

## LUT Format

The LUT should be stored as a list of samples:

```python
samples = [
    ((robot_x_1, robot_y_1), (aim_x_1, aim_y_1)),
    ((robot_x_2, robot_y_2), (aim_x_2, aim_y_2)),
    ...
]
```

You can hardcode it, load it from JSON, or generate it from a constants file.

## Runtime Behavior

### 1. Get current robot position

Read the robot's current field pose:

- `robotX`
- `robotY`

### 2. Interpolate a virtual aim point from the LUT

Given the current robot position, interpolate an aim point from nearby LUT samples.

Recommended method:

- compute distance from the robot position to every LUT sample position
- choose the nearest `k` samples, usually `k = 3`
- use inverse-distance weighting

For each sample:

```text
weight = 1 / distance^2
```

Then:

```text
aimX = weighted average of sample aim X values
aimY = weighted average of sample aim Y values
```

Special case:

- if the robot is essentially exactly on a sample point, return that sample's aim point directly

### 3. Compute turret target angle

Once the interpolated virtual aim point is found:

```text
dx = aimX - robotX
dy = aimY - robotY
fieldAngle = atan2(dy, dx)
turretTarget = normalize(fieldAngle - robotHeading)
```

If the turret controller wants a global heading instead of a relative heading, use `fieldAngle` directly.

## Pseudocode

```python
def get_virtual_aim_point(robot_x, robot_y, lut_samples, neighbor_count=3):
    weighted = []

    for (sample_x, sample_y), (aim_x, aim_y) in lut_samples:
        dx = robot_x - sample_x
        dy = robot_y - sample_y
        distance = hypot(dx, dy)

        if distance < 1e-6:
            return aim_x, aim_y

        weighted.append((distance, aim_x, aim_y))

    weighted.sort(key=lambda entry: entry[0])
    neighbors = weighted[:neighbor_count]

    total_weight = 0.0
    sum_x = 0.0
    sum_y = 0.0

    for distance, aim_x, aim_y in neighbors:
        weight = 1.0 / (distance * distance)
        total_weight += weight
        sum_x += aim_x * weight
        sum_y += aim_y * weight

    return sum_x / total_weight, sum_y / total_weight


def get_turret_target(robot_x, robot_y, robot_heading, lut_samples):
    aim_x, aim_y = get_virtual_aim_point(robot_x, robot_y, lut_samples)
    dx = aim_x - robot_x
    dy = aim_y - robot_y
    field_angle = atan2(dy, dx)
    return normalize_angle(field_angle - robot_heading)
```

## Interaction With Shoot-On-The-Move

If the robot also supports shoot-on-the-move compensation, keep the concepts separate.

Recommended order:

1. decide whether turret heading is computed from the real robot pose or a motion-compensated pose
2. get the virtual aim point from the LUT
3. compute the angle from the chosen pose to that virtual aim point

Important:

- the LUT still represents a **position-based desired target**
- shoot-on-the-move is a **separate compensation layer**

Do not replace the LUT with a velocity-based correction.

## Tuning Guidance

The best LUT samples come from real shots, not guessed values.

Recommended workflow:

1. move the robot to a known field location
2. shoot using center-goal aiming and observe the miss
3. adjust the virtual aim point until the shot scores consistently
4. save that `(robot position) -> (aim point)` pair
5. repeat across the useful shooting area

Best practices:

- collect more points in shallow-angle regions where misses are large
- collect fewer points where center aiming already works
- keep left and right side samples balanced if the field use is symmetric
- use the same pose-estimation coordinate frame in tuning and runtime

## Failure Modes To Avoid

- using distance-only correction instead of position-based correction
- mixing coordinate systems between tuned samples and runtime localization
- applying turret-relative offsets when the LUT values were tuned in field coordinates
- using too few points in difficult regions
- allowing one bad sample to distort a large area

## Recommended Implementation Notes

- keep the LUT in its own class/module, for example `PositionAimLut`
- expose a function like `getVirtualAimPoint(robotPose)` or `getTurretTargetAngle(robotPose)`
- make it easy to disable LUT aiming for testing
- log the selected / interpolated aim point during tuning
- if alliance matters, either maintain separate LUTs or transform coordinates consistently

## What The Implementing Agent Should Build

Another agent working in the robot code should implement:

1. a data structure holding `((robot_x, robot_y), (aim_x, aim_y))` samples
2. nearest-neighbor inverse-distance interpolation
3. conversion from interpolated aim point to turret target angle
4. a switch to enable / disable LUT aiming
5. optional telemetry:
   - robot pose
   - chosen neighbors
   - interpolated aim point
   - final turret target angle

## Summary

This is a **field-position-based turret aiming system**.

It does **not** ask:

- "How far am I from the goal?"

It asks:

- "From this robot position on the field, what point should I really aim at so the shot goes in?"

That virtual aim point is interpolated from tuned samples, and the turret points at that point instead of the goal center.
