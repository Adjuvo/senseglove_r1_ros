# SenseGlove R1 ROS
ROS 2 integration for the SenseGlove R1 haptic glove

This package is a ROS 2 wrapper around the [SenseGlove R1 Python API](https://github.com/Adjuvo/SenseGlove-R1-API) that publishes glove state data and subscribes per-finger active force feedback (A-FFB) commands. It also includes the [Robot Hand Mapper (RHM)](docs/robot-hand-mapper.md), a simple pinch-based mapper for position controlling a 6DoF robot hand. For full API reference, see the [SenseGlove API docs](https://adjuvo.github.io/SenseGlove-R1-API/api-reference/).

## Initial Setup

See **[Initial Setup](docs/setup-initial.md)** for workspace setup, installing dependencies, udev rules, and WSL setup (Windows).

## Launch

```bash
# Real hardware, 1 glove (default)
ros2 launch r1_bringup r1.launch.py

# Real hardware, 2 gloves
ros2 launch r1_bringup r1.launch.py num_gloves:=2

# Simulation mode
ros2 launch r1_bringup r1.launch.py use_simulation:=true

# Without displaying the Robot Hand Mapper Pinch GUI
ros2 launch r1_bringup r1.launch.py display_rhm_pinch_gui:=false
```
> [!NOTE]
> The r1_manager node can be run standalone as well: `ros2 run r1_interaction r1_manager`

### Launch Arguments

| Argument                  | Default   | Description                               |
|:---                       |:---       |:---                                       |
| `num_gloves`              | `1`       | Number of gloves to connect               |
| `use_simulation`          | `false`   | Run in simulation mode without hardware   |
| `display_rhm_pinch_gui`   | `true`    | Show the RHM pinch calibration GUI        |


## Topics

![Publisher](https://img.shields.io/badge/Publisher-/r1/glove{id}/{lh|rh}/glove_states-blue?style=flat-square)
![Type](https://img.shields.io/badge/Type-r1_msgs/R1GloveState-orange?style=flat-square)


| Field | Type | Description |
|:---                                   |:---                           |:---                                                                               |
| `header`                              | `std_msgs/Header`             | Timestamp                                                                         |
| `finger_names`                        | `string[]`                    | Ordered finger labels                                                             |
| `joint_angles`                        | `Float64MultiArray`           | Joint angles `[rad]`, shape `[fingers × joints]`                                  |
| `finger_tip_positions`                | `geometry_msgs/Point[]`       | Fingertip positions w.r.t the finger base origin `[mm]`                           |
| `finger_tip_orientations`             | `geometry_msgs/Quaternion[]`  | Fingertip orientations w.r.t the finger base origin                               |
| `finger_distances`                    | `float64[]`                   | Thumb-to-`[index, middle, ring, pinky]` tip distances `[mm]`                      |
| `normalized_finger_positions`         | `float64[]`                   | Flexion + abduction `[0–10000]` - `[Flex (Thumb-to-Pinky), abd (Thumb-to-Pinky)]`  |
| `normalized_finger_positions_pinch`   | `float64[]`                   | Remapped norms via active **RHM pinch config**                                    |
| `sensed_forces`                       | `float64[]`                   | Sensed forces for `[thumb, index, middle, ring]` `[mN]`                           |

### Force Commands

![Subscriber](https://img.shields.io/badge/Subscriber-/r1/glove{id}/{lh|rh}/force_commands-blue?style=flat-square)
![Type](https://img.shields.io/badge/Type-r1_msgs/R1ForceCommands-orange?style=flat-square)

| Field             | Type      | Description                               |
|:---               |:---       |:---                                       |
| `force_values`    | `int32[]` | Target force per actuated finger `[mN]`   |
