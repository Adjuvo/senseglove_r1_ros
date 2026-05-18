# R1GloveState.msg
# A message for streaming R1 Hand State

std_msgs/Header header
string[] finger_names

# Exoskeleton joint angles [rad]
std_msgs/Float64MultiArray joint_angles

# Fingertip Cartesian positions in the glove's local frame [mm]
geometry_msgs/Point[] finger_tip_positions

# Fingertip orientations as unit quaternions (x, y, z, w)
geometry_msgs/Quaternion[] finger_tip_orientations

# Euclidean distances from the thumb tip to each other fingertip [index, middle, ring, pinky] [mm]
float64[] finger_distances

# Flexion/abduction Percentage Bents
# [flexion_thumb, flexion_index, flexion_middle, flexion_ring, flexion_pinky,
# abduction_thumb, abduction_index, abduction_middle, abduction_ring, abduction_pinky] Range: [0-10000]
float64[] normalized_finger_positions

# Flexion/abduction percentages remapped through the RobotHandMapper (RHM) pinch config
# [flexion_thumb, flexion_index, flexion_middle, flexion_ring, flexion_pinky, 
# abduction_thumb, abduction_index, abduction_middle, abduction_ring, abduction_pinky] Range: [0-10000]
float64[] normalized_finger_positions_pinch

# Currently sensed forces for each finger [thumb, index, middle, ring] [mN]
float64[] sensed_forces