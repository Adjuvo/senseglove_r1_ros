# Releases

# v0.1.1
- ROS-param: "DeviceID:handedness" pair for connected gloves

# v0.1.0
- Reorganized `r1_interaction`/`r1_bringup` into a single `r1_ros` package
- `r1_manager` now stamps every `R1GloveState` with `header.stamp` and `finger_names`
- Removed handedness (`lh`/`rh`) from topics
- Added a `use_filter` launch parameter to toggle the SUSPICION tracking filter (0.25 EWMA smoothing)
- Split `r1_pro_ros` version
- Added unit test suites

# v0.0.2

- Removed RobotHandMapper (RHM): pinch configs (Seed, DG5F left/right), `SetRHMConfig` service, RHM GUI params, and docs
- Added TouchLab haptic feedback controller (`touchlab_haptic_node`) with calibration and new touchlab_haptic.launch.py (hand, glove_id, port args)
- `R1GloveState`: renamed `normalized_finger_positions` -> `percentage_bents`, removed `normalized_finger_positions_pinch`, added `finger_joint_distances`, `percentage_bent_proximal`, `percentage_bent_distal`

# v0.0.1

- ROS2 package for the SenseGlove R1 glove. Tested in Jazzy.
- R1 manager node with per-device topic naming: `/r1/glove{id}/{lh|rh}/`
- RobotHandMapper (RHM) with pinch configs (Seed, DG5F left/right)
- Haptic force control node with GUI slider