#!/usr/bin/env python3

import math
import time

from rclpy.node import Node
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from std_srvs.srv import Trigger

CALIBRATION_DURATION = 5.0

class TouchlabCalibration:

    def __init__(self, node: Node, n_fingers: int, finger_names: list[str]):
        self.node = node
        self.n_fingers = n_fingers
        self.finger_names = finger_names
        self.offsets: list[float] = [0.0] * n_fingers
        self.calibrating = False
        self._samples: list[list[float]] = [[] for _ in range(n_fingers)]

    def register_service(self, service_name: str, callback_group) -> None:
        self.node.create_service(
            Trigger, service_name, self._service_cb,
            callback_group=callback_group,
        )
        self.node.get_logger().info(f"Calibration service registered at '{service_name}'")

    def _service_cb(self, request, response):
        if self.calibrating:
            response.success = False
            response.message = "Calibration already in progress"
            return response
        success, message = self.run()
        response.success = success
        response.message = message
        return response
    
    def accumulate(self, finger_idx: int, raw_taxels: list) -> None:
        if self.calibrating:
            mag = math.sqrt(sum(v * v for v in raw_taxels))
            self._samples[finger_idx].append(mag)

    def run(self) -> tuple[bool, str]:
        self.node.get_logger().info(
            f"Calibration started: Do not move; keep all sensors at rest for {CALIBRATION_DURATION:.0f} s"
        )
        self._samples = [[] for _ in range(self.n_fingers)]
        self.calibrating = True
        time.sleep(CALIBRATION_DURATION)
        self.calibrating = False
        return self._compute()

    def _compute(self) -> tuple[bool, str]:
        any_missing = False
        for i in range(self.n_fingers):
            samples = self._samples[i]
            if not samples:
                self.node.get_logger().warn(
                    f"No samples collected for '{self.finger_names[i]}': offset unchanged"
                )
                any_missing = True
                continue
            self.offsets[i] = sum(samples) / len(samples)
            self.node.get_logger().info(
                f"  {self.finger_names[i]}: {len(samples)} samples, "
                f"baseline mag = {self.offsets[i]:.1f}"
            )

        if any_missing:
            return False, "Calibration incomplete: no samples for some fingers"
        return True, "Calibration complete"
