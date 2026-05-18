"""
Robot Hand Pinch Configuration
"""

from SG_API.SG_robot_hand_mapper import PinchConfig

DG5FPinchConfigLeft = PinchConfig(
    name="DG5FPinchConfigLeft",
    # Robot Hand Pinch Targets (from percentage bent values)
    # Format: Finger_index: [thumb_abduction, thumb_flexion, finger_flexion]
    robot_pinch_targets={
        1: [7300.000,  4500.000, 4400.000],  # Pinch Index
        2: [8500.000,  5000.000, 4850.000],  # Pinch Middle
        3: [10000.000,  5500.000, 4850.000],  # Pinch Ring
        4: [10000.000, 6500.000, 6800.000],  # Pinch Pinky
    },

    # Pinch detection parameters
    # Minimum thumb abduction to start considering pinch
    thumb_abduction_threshold=5500,
    distance_thresholds={
        "enter_distance": 40,
        "exit_distance": 55,
        "min_distance": 25,
        "max_distance": 70,
    },

    # Blending and detection settings
    # Weight between thumb abduction and distance influence (0 = only distance, 1 = only thumb)
    blend_weight=0.6,
    primary_pinch_finger=1,     # 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky

)

config = DG5FPinchConfigLeft
