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

# Distances from the thumb tip to each joint [MCP, PIP, DIP, FINGERTIP] along
# every other finger's whole chain (not just its tip) [index, middle, ring, pinky] [mm]
std_msgs/Float64MultiArray finger_joint_distances

# Flexion/abduction Percentage Bents
# [flexion_thumb, flexion_index, flexion_middle, flexion_ring, flexion_pinky,
# abduction_thumb, abduction_index, abduction_middle, abduction_ring, abduction_pinky] Range: [0-10000]
float64[] percentage_bents

# Proximal-only flexion Percentage Bent (clawing feature)
# Sums the angles of joint 1 through joint 3, instead of the whole finger
# [thumb, index, middle, ring, pinky] Range: [0-10000]
float64[] percentage_bent_proximal

# Distal-only flexion Percentage Bent (clawing feature)
# Sums the angles of joint 5 through the fingertip only, instead of the whole finger
# [thumb, index, middle, ring, pinky] Range: [0-10000]
float64[] percentage_bent_distal

# Currently sensed forces for each finger [thumb, index, middle, ring] [mN]
float64[] sensed_forces