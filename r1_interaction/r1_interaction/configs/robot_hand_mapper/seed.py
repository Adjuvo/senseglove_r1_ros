"""
Robot Hand Pinch Configuration
"""

from SG_API.SG_robot_hand_mapper import PinchConfig

Seed = PinchConfig(
    name="Seed",
    # Robot Hand Pinch Targets (from percentage bent values)
    # Format: Finger_index: [thumb_abduction, thumb_flexion, finger_flexion]
    robot_pinch_targets={
        1: [10000.000, 4300.000, 6550.000],  # Pinch Index
        2: [10000.000, 6000.000, 7090.000],  # Pinch Middle
        3: [10000.000, 4786.000, 5857.000],  # Pinch Ring
        4: [10000.000, 5484.000, 5465.000],  # Pinch Pinky
    },

    # Pinch detection parameters
    # Minimum thumb abduction to start considering pinch
    thumb_abduction_threshold=5000,
    distance_thresholds={
        "enter_distance": 40.0,
        "exit_distance": 55.0,
        "min_distance": 10.0,
        "max_distance": 55.0,
    },

    # Blending and detection settings
    # Weight between thumb abduction and distance influence (0 = only distance, 1 = only thumb)
    blend_weight=0.6,
    primary_pinch_finger=1,     # 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky

)

config = Seed
