#!/usr/bin/env python3

import math
import time
import socket
from threading import Thread

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

import touchlab_comm_py as tl

from r1_msgs.msg import R1ForceCommands
from r1_interaction.haptics.touchlab_calibration import TouchlabCalibration

FINGER_NAMES = ["thumb", "index", "middle", "ring"]
N_FINGERS = len(FINGER_NAMES)
N_TAXELS = 19

# Teleplot
_teleplot_addr = ("127.0.0.1", 47269)
_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def _send_telemetry(name, value):
    now = time.time() * 1000
    _sock.sendto(f"{name}:{now:.0f}:{value}|g".encode(), _teleplot_addr)

# EWMA filter Asymmetric
class _EWMA:
    def __init__(self, alpha=0.3, alpha_decay=None):
        self.alpha = alpha
        self.alpha_decay = alpha_decay if alpha_decay is not None else alpha
        self._v = 0.0

    def update(self, x):
        a = self.alpha if float(x) >= self._v else self.alpha_decay
        self._v = a * float(x) + (1.0 - a) * self._v
        return self._v

    def reset(self):
        self._v = 0.0

def _line_through_2points(x1, y1, x2, y2, x):
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    return m * x + b


class TouchLabHapticController(Node):
    def __init__(self):
        super().__init__("touchlab_haptic_node")
        self.get_logger().info("Starting TouchLab Haptic Controller...")

        self.declare_parameter("hand", "left")
        self.declare_parameter("glove_id", 73)
        self.declare_parameter("port", "/dev/ttyACM0")
        self.declare_parameter("calib_file", "")
        self.declare_parameter("timeout", 500)

        self.declare_parameter("ewma_alpha", 0.25)
        self.declare_parameter("ewma_alpha_decay", 0.8)

        self.declare_parameter("min_force_goal", 0)
        self.declare_parameter("max_force_goal", 20000)
        self.declare_parameter("gain", 0.7)
        self.declare_parameter("thumb_gain", 1.5)

        self.declare_parameter("force_threshold", 500.0)
        self.declare_parameter("force_mag_max", 70000.0)
        self.declare_parameter("solid_obj_start_mag", 4000.0)

        hand = self.get_parameter("hand").get_parameter_value().string_value
        if hand not in ("left", "right"):
            raise ValueError(f"Invalid 'hand' parameter: '{hand}'")

        glove_id = self.get_parameter("glove_id").get_parameter_value().integer_value
        port = self.get_parameter("port").get_parameter_value().string_value
        calib_file = self.get_parameter("calib_file").get_parameter_value().string_value
        self.sensor_timeout = self.get_parameter("timeout").get_parameter_value().integer_value
        
        alpha = self.get_parameter("ewma_alpha").get_parameter_value().double_value
        alpha_decay = self.get_parameter("ewma_alpha_decay").get_parameter_value().double_value
        
        self.min_force_goal = self.get_parameter("min_force_goal").get_parameter_value().integer_value
        self.max_force_goal = self.get_parameter("max_force_goal").get_parameter_value().integer_value
        self.gain = self.get_parameter("gain").get_parameter_value().double_value
        self.thumb_gain = self.get_parameter("thumb_gain").get_parameter_value().double_value

        self.force_threshold = self.get_parameter("force_threshold").get_parameter_value().double_value
        self.force_mag_max = self.get_parameter("force_mag_max").get_parameter_value().double_value
        self.solid_obj_start_mag = self.get_parameter("solid_obj_start_mag").get_parameter_value().double_value

        side = "lh" if hand == "left" else "rh"
        haptic_topic = f"/r1/glove{glove_id}/{side}/force_commands"

        self._ewma = [_EWMA(alpha=alpha, alpha_decay=alpha_decay) for _ in range(N_FINGERS)]

        try:
            self._com = tl.TouchlabComms()
            self._com.init(calib_file)
            self._com.connect(port)
        except RuntimeError as exc:
            self.get_logger().error(f"Failed to connect on {port}: {exc}")
            raise

        self.get_logger().info(f"Connected on {port}")

        self._calibration = TouchlabCalibration(self, N_FINGERS, list(FINGER_NAMES))

        self._pub = self.create_publisher(R1ForceCommands, haptic_topic, 1)
        self._calibration.register_service(
            "~/calibrate", MutuallyExclusiveCallbackGroup(),
        )

        self.get_logger().info(f"Haptic topic: {haptic_topic}")


    def _mag_to_force_goal(self, mag, ewma, gain=None):
        filtered = ewma.update(mag) * (gain if gain is not None else self.gain)

        if filtered < self.force_threshold:
            return self.min_force_goal

        f = filtered
        if self.solid_obj_start_mag > 0.0 and f > self.solid_obj_start_mag:
            goal_at_start = _line_through_2points(
                self.force_threshold, self.min_force_goal,
                self.force_mag_max, self.max_force_goal, self.solid_obj_start_mag
            )
            goal = _line_through_2points(
                self.solid_obj_start_mag, goal_at_start,
                self.force_mag_max, float(self.max_force_goal) * 2.0, f
            )
        else:
            goal = _line_through_2points(
                self.force_threshold, self.min_force_goal,
                self.force_mag_max, self.max_force_goal, f
            )

        return int(max(float(self.min_force_goal), min(float(self.max_force_goal), goal)))

    def _startup_calibration(self):
        time.sleep(0.5)
        self._calibration.run()

    def _publish_zeros(self):
        msg = R1ForceCommands()
        msg.force_values = [0] * N_FINGERS
        self._pub.publish(msg)

    def run(self):
        self.get_logger().info("Sensor read loop started")
        Thread(target=self._startup_calibration, daemon=True).start()
        try:
            while rclpy.ok():
                try:
                    data = self._com.read_raw(self.sensor_timeout)
                except Exception as exc:
                    self.get_logger().error(f"Read error: {exc}")
                    break

                if not data:
                    self.get_logger().warning("Empty read: sensor not responding")
                    continue

                goals = []
                for i in range(N_FINGERS):
                    raw_group = list(data[(i + 1) * N_TAXELS : (i + 2) * N_TAXELS])
                    raw_mag = math.sqrt(sum(val * val for val in raw_group))
                    self._calibration.accumulate(i, raw_group)

                    if self._calibration.calibrating:
                        goals.append(0)
                        continue

                    zeroed_mag = max(0.0, raw_mag - self._calibration.offsets[i])
                    _send_telemetry(f"mag_{FINGER_NAMES[i]}", zeroed_mag)

                    gain = self.thumb_gain if i == 0 else self.gain
                    clamped = self._mag_to_force_goal(zeroed_mag, self._ewma[i], gain)
                    goals.append(clamped)

                msg = R1ForceCommands()
                msg.force_values = goals
                self._pub.publish(msg)
        finally:
            self._publish_zeros()


def main(args=None):
    rclpy.init(args=args)
    node = TouchLabHapticController()

    executor = MultiThreadedExecutor()
    executor.add_node(node)
    spin_thread = Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        executor.shutdown()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
