"""
Adapter-correctness tests for R1Manager._build_state_msg().
"""
import numpy as np

from SG_API import SG_main
from SG_API import SG_simulator as SG_sim

from r1_ros.main.r1_manager import R1Manager, FINGER_NAMES

# 'links_all_straight' golden pose, from rembrandt-api/Tests_SG_API/test_kinematics.py.
_LINKS_ALL_STRAIGHT_ANGLES_RAD = [
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.5707963267948966],
] * 5
# Known-good abduction percentage-bents for the pose above, same source.
_LINKS_ALL_STRAIGHT_EXPECTED_ABD_PERC_BENTS = [0, 4879, 4339, 4315, 2720]


def _set_pose(device_id, exo_angles_rad):
    device_info = SG_main.get_device_info(device_id)
    SG_sim.set_angles_rad(device_info, exo_angles_rad)


def test_build_state_msg_matches_live_sg_api_getters(sim_device_id, stub_r1_manager):
    _set_pose(sim_device_id, _LINKS_ALL_STRAIGHT_ANGLES_RAD)

    msg = R1Manager._build_state_msg(stub_r1_manager, sim_device_id)

    assert list(msg.finger_names) == FINGER_NAMES

    # joint_angles: Float64MultiArray, flattened (fingers, joints)
    expected_angles = np.array(SG_main.get_exo_angles_rad(sim_device_id))
    assert [d.size for d in msg.joint_angles.layout.dim] == list(expected_angles.shape)
    actual_angles = np.array(msg.joint_angles.data).reshape(expected_angles.shape)
    np.testing.assert_allclose(actual_angles, expected_angles)

    # fingertip positions/orientations
    expected_pos, expected_rot = SG_main.get_fingertips_pos_rot(sim_device_id)
    assert len(msg.finger_tip_positions) == len(expected_pos)
    for p_msg, p_expected in zip(msg.finger_tip_positions, expected_pos):
        np.testing.assert_allclose([p_msg.x, p_msg.y, p_msg.z], p_expected)
    assert len(msg.finger_tip_orientations) == len(expected_rot)
    for q_msg, q_expected in zip(msg.finger_tip_orientations, expected_rot):
        np.testing.assert_allclose([q_msg.x, q_msg.y, q_msg.z, q_msg.w], q_expected)

    # finger_distances
    expected_distances = [float(x) for x in SG_main.get_fingertip_distances(sim_device_id)]
    np.testing.assert_allclose(list(msg.finger_distances), expected_distances)

    # finger_joint_distances
    expected_jd = np.array(SG_main.get_thumb_to_finger_joint_distances(sim_device_id))
    assert [d.size for d in msg.finger_joint_distances.layout.dim] == list(expected_jd.shape)
    actual_jd = np.array(msg.finger_joint_distances.data).reshape(expected_jd.shape)
    np.testing.assert_allclose(actual_jd, expected_jd)

    # sensed_forces
    expected_forces = [float(x) for x in SG_main.get_forces_sensed(sim_device_id)]
    np.testing.assert_allclose(list(msg.sensed_forces), expected_forces)

    # header.stamp: just check get_clock() produced a real, non-zero stamp.
    assert msg.header.stamp.sec > 0 or msg.header.stamp.nanosec > 0


def test_percentage_bent_values_match_golden_table(sim_device_id, stub_r1_manager):
    """Cross-checks percentage_bents' abduction half against SG_API's kinematics golden table."""
    _set_pose(sim_device_id, _LINKS_ALL_STRAIGHT_ANGLES_RAD)

    msg = R1Manager._build_state_msg(stub_r1_manager, sim_device_id)

    np.testing.assert_allclose(
        list(msg.percentage_bents)[5:],
        _LINKS_ALL_STRAIGHT_EXPECTED_ABD_PERC_BENTS,
    )
