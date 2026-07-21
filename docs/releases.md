# Releases

# v0.0.2

- Removed RobotHandMapper (RHM): pinch configs (Seed, DG5F left/right), `SetRHMConfig` service, RHM GUI params, and docs
- Added TouchLab haptic feedback controller (`touchlab_haptic_node`) with calibration and new touchlab_haptic.launch.py (hand, glove_id, port args)
- `R1GloveState`: renamed `normalized_finger_positions` -> `percentage_bents`, removed `normalized_finger_positions_pinch`, added `finger_joint_distances`, `percentage_bent_proximal`, `percentage_bent_distal`

# v0.0.1

- ROS2 package for the SenseGlove R1 glove. Tested in Jazzy.
- R1 manager node with per-device topic naming: `/r1/glove{id}/{lh|rh}/`
- RobotHandMapper (RHM) with pinch configs (Seed, DG5F left/right)
- Haptic force control node with GUI slider