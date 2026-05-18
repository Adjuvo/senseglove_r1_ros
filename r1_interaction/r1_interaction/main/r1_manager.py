#!/usr/bin/env python3
"""
ROS 2 node for publishing R1 glove states and subscribing to force commands.
Device IDs and handedness are auto-detected from the API.

Publishes:  /r1/glove{device_id}/{lh|rh}/glove_states   (R1GloveState)
Subscribes: /r1/glove{device_id}/{lh|rh}/force_commands (R1ForceCommands)

Parameters:
    num_gloves            (int,  default 1)    — gloves to wait for before continuing
    use_simulation        (bool, default true) — use simulated glove(s) instead of USB
    display_rhm_pinch_gui (bool, default true) — show 3D exo + pinch mapper GUI
    rhm_gui_device_id     (int,  default -1)   — device to show in the GUI at startup (-1 = first device)
                                                  :ros2 param set /r1_manager rhm_gui_device_id <id>

Note: RobotHandMapper (RHM) is always created for all devices (rhm_percentage_bents data is always present in state msg).
      The set_rhm_config service handles per-device PinchConfig assignment at runtime.
"""

import sys
import traceback
import threading
import numpy as np
from PySide6.QtWidgets import QApplication

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Float64MultiArray, MultiArrayLayout, MultiArrayDimension
from geometry_msgs.msg import Point, Quaternion

from SG_API import SG_main, SG_types as SG_T

from r1_msgs.msg import R1GloveState, R1ForceCommands
from r1_interaction.main.r1_rhm import R1RHM

class R1Manager(Node):
    def __init__(self, use_best_effort_qos: bool = False):
        super().__init__('r1_manager')
        self.get_logger().info(f"Initializing: {self.get_name()}")

        # Parameters
        self.declare_parameter('num_gloves', 1)
        self.declare_parameter('use_simulation', False)
        self.declare_parameter('display_rhm_pinch_gui', True)
        self.declare_parameter('rhm_gui_device_id', -1)

        num_gloves = self.get_parameter('num_gloves').get_parameter_value().integer_value
        use_simulation = self.get_parameter('use_simulation').get_parameter_value().bool_value
        display_rhm_pinch_gui = self.get_parameter('display_rhm_pinch_gui').get_parameter_value().bool_value

        com_type = SG_T.Com_type.SIMULATED_GLOVE if use_simulation else SG_T.Com_type.REAL_GLOVE_USB
        if use_simulation:
            self.get_logger().info("Using simulated glove mode")

        # Init API
        device_ids = SG_main.init(num_gloves, com_type)
        self.get_logger().info(f"SG_main.init() returned device IDs: {device_ids}")

        # QoS
        if use_best_effort_qos:
            qos = QoSProfile(
                reliability=ReliabilityPolicy.BEST_EFFORT,
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
                durability=DurabilityPolicy.VOLATILE,
            )
        else:
            qos = QoSProfile(depth=10)

        # Per-device setup
        self._devices: list[dict] = []
        for device_id in device_ids:
            handedness_str = 'lh' if SG_main.get_handedness(device_id) == SG_T.Hand.LEFT else 'rh'

            state_pub = self.create_publisher(
                R1GloveState,
                f"/r1/glove{device_id}/{handedness_str}/glove_states",
                qos,
            )

            force_sub = self.create_subscription(
                R1ForceCommands,
                f"/r1/glove{device_id}/{handedness_str}/force_commands",
                lambda msg, device_id=device_id: self._force_callback(device_id, msg),  
                qos,
            )

            # Check per-device simulation mode
            if SG_main.get_COM_type(device_id) == SG_T.Com_type.SIMULATED_GLOVE:
                SG_main.SG_sim.set_mode(device_id, SG_main.SG_sim.Simulation_Mode.FINGERS_OPEN_CLOSE)

            nr_fingers_force = SG_main.nr_of_fingers_force(device_id)

            self._devices.append({
                'device_id':        device_id,
                'handedness':       handedness_str,
                'state_pub':        state_pub,
                'force_sub':        force_sub,
                'nr_fingers_force': nr_fingers_force,
            })

            self.get_logger().info(f"Initialized R1 [{handedness_str}] device_id={device_id}")

        self._device_map: dict[int, dict] = {d['device_id']: d for d in self._devices}

        # RobotHandMapper
        self._rhm = R1RHM(device_ids, display_gui=display_rhm_pinch_gui, node=self)
        self.get_logger().info(f"RobotHandMapper initialized for devices: {device_ids}")
        for device_id, config_name in self._rhm._current_assignments.items():
            self.get_logger().info(f"Device_id={device_id}: Applied RHM config: '{config_name}'")

        # RHM GUI
        initial_display = self.get_parameter('rhm_gui_device_id').get_parameter_value().integer_value
        if initial_display == -1:
            initial_display = device_ids[0]
        self._rhm.set_displayed_device(initial_display)
        self.add_on_set_parameters_callback(self._on_parameter_change)

        # Register callback for new data
        self._shutting_down = False
        SG_main.subscr_r1_data_callback(self._on_new_data)

    def _on_parameter_change(self, params):
        for param in params:
            if param.name == 'rhm_gui_device_id':
                device_id = param.value
                if device_id not in self._device_map:
                    return SetParametersResult(successful=False, reason=f"Unknown device_id {device_id}")
                self._rhm.set_displayed_device(device_id)
                self.get_logger().info(f"Displaying GUI for device_id={device_id}")
        return SetParametersResult(successful=True)

    # Collect glove data and publish it as a R1GloveState message
    def _on_new_data(self, device_id: int):
        if self._shutting_down or not rclpy.ok():
            return
        
        device = self._device_map.get(device_id)
        if device is None:
            return
        
        state_msg = self._build_state_msg(device_id)
        device['state_pub'].publish(state_msg)
        self._rhm.update_gui(device_id)

    def _build_state_msg(self, device_id: int) -> R1GloveState:
        state_msg = R1GloveState()

        # Joint angles
        angles_rad = SG_main.get_exo_angles_rad(device_id)
        angles_rad_array = np.array(angles_rad)

        joint_array = Float64MultiArray()
        joint_array.layout = MultiArrayLayout(
            dim=[
                MultiArrayDimension(label='fingers', size=angles_rad_array.shape[0], stride=angles_rad_array.size),
                MultiArrayDimension(label='joints',  size=angles_rad_array.shape[1], stride=angles_rad_array.shape[1]),
            ],
            data_offset=0
        )

        joint_array.data = angles_rad_array.flatten().tolist()
        state_msg.joint_angles = joint_array        

        # Fingertip positions and orientations
        finger_tip_pos, finger_tip_rot = SG_main.get_fingertips_pos_rot(device_id)
        state_msg.finger_tip_positions = [Point(x=p[0], y=p[1], z=p[2]) for p in finger_tip_pos]
        state_msg.finger_tip_orientations = [Quaternion(x=q[0], y=q[1], z=q[2], w=q[3]) for q in finger_tip_rot]

        # Finger distances: thumb to [index, middle, ring, pinky]
        state_msg.finger_distances = [float(x) for x in SG_main.get_fingertip_distances(device_id)]

        # Percentage Bent (0–10000)
        flexion_perc_bents, abduction_perc_bents = SG_main.get_percentage_bents(device_id)
        state_msg.normalized_finger_positions = [float(x) for x in [*flexion_perc_bents, *abduction_perc_bents]]

        #  Percentage Bent (0–10000) for pinch (from RobotHandMapper)
        flexion_perc_bents_pinch, abduction_perc_bents_pinch = SG_main.get_rhm_percentage_bents(device_id)
        state_msg.normalized_finger_positions_pinch = [float(x) for x in [*flexion_perc_bents_pinch, *abduction_perc_bents_pinch]]

        # Sensed forces (thumb, index, middle, ring)
        state_msg.sensed_forces = [float(x) for x in SG_main.get_forces_sensed(device_id)]

        return state_msg

    def _force_callback(self, device_id: int, msg: R1ForceCommands):
        device = self._device_map.get(device_id)
        if device is None:
            return
        
        force_values = list(msg.force_values)
        if len(force_values) != device['nr_fingers_force']:
            self.get_logger().warn(f"Got {len(force_values)} force values, expected {device['nr_fingers_force']}. Skipping.")
            return
        
        try:
            SG_main.set_force_goals(device_id=device_id, force_goals=force_values)
        except Exception:
            self.get_logger().error(f"Error in _force_callback: {traceback.format_exc()}")

    def destroy_node(self):
        self._shutting_down = True
        self.get_logger().info("Shutting down R1Manager...")
        if self._rhm:
            self._rhm.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv)
    node = R1Manager()
    display_rhm_pinch_gui = node.get_parameter('display_rhm_pinch_gui').get_parameter_value().bool_value

    def _shutdown():
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    if display_rhm_pinch_gui:
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        ros_thread = threading.Thread(target=executor.spin, daemon=True)
        ros_thread.start()
        app.aboutToQuit.connect(_shutdown)
        try:
            app.exec()
        except KeyboardInterrupt:
            _shutdown()
    else:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            _shutdown()

if __name__ == '__main__':
    main()