#!/usr/bin/env python3
"""
RobotHandMapper (RHM) = maps glove finger flexion to robot hand control values.

When a pinch is detected, the glove's percentage-bent values are gradually
remapped to pre-calibrated robot hand targets (defined in a PinchConfig).
Outside of a pinch the raw glove values pass through unchanged.

This module wraps per-device RobotHandMapper instances and owns the optional
3D exo + PinchMapper GUI window. It lives in the same process as R1Manager.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import QObject, Signal

from rclpy.node import Node
from SG_API import SG_main, SG_types as SG_T
from SG_API import SG_GUI as GUI
from SG_API.SG_robot_hand_mapper import PinchConfig
from r1_msgs.srv import SetRHMConfig
from r1_interaction.configs.robot_hand_mapper.seed import Seed
from r1_interaction.configs.robot_hand_mapper.dg5f_pinch_config_left import DG5FPinchConfigLeft
from r1_interaction.configs.robot_hand_mapper.dg5f_pinch_config_right import DG5FPinchConfigRight

# Available PinchConfigs
CONFIGS: dict[str, PinchConfig] = {
    "Seed": Seed,
    "DG5FPinchConfigLeft": DG5FPinchConfigLeft,
    "DG5FPinchConfigRight": DG5FPinchConfigRight
}

_default_config_left = DG5FPinchConfigLeft
_default_config_right = DG5FPinchConfigRight

# ---------------------------------------------------------------------------
class _GUIBridge(QObject):
    """Thread-safe bridge: emits signals from the ROS callback thread;
    Qt delivers them to RHMGUI on the main thread."""
    update_signal = Signal(int)
    switch_device_signal = Signal(int)

    def __init__(self, gui: _RHMGUI):
        super().__init__()
        self.update_signal.connect(gui.update)
        self.switch_device_signal.connect(gui.set_displayed_device)

# ---------------------------------------------------------------------------
class _RHMGUI(QWidget):
    def __init__(self, device_ids: list[int]):
        super().__init__()
        self._device_ids = set(device_ids)
        self._displayed_device_id = device_ids[0]
        self._last_title = ""

        self.setWindowTitle("R1 GUI")
        self.setGeometry(100, 100, 1600, 700)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 3D exoskeleton display (left)
        self._gui_3d = GUI.UI_Exo_Display()
        layout.addWidget(QWidget.createWindowContainer(self._gui_3d), 6)

        # Pinch widget
        self._pinch_widgets: dict[int, QWidget] = {}
        for device_id in device_ids:
            w = SG_main.create_rhm_pinch_gui(device_id)
            w.setMaximumWidth(600)
            layout.addWidget(w, 1)
            w.setVisible(device_id == self._displayed_device_id)
            self._pinch_widgets[device_id] = w

        exo_poss, _ = SG_main.get_exo_joints_poss_rots(self._displayed_device_id)
        self._gui_3d.create_hand_exo(exo_poss)
        self.show()

    def set_displayed_device(self, device_id: int):
        """Switch which device is shown"""
        if device_id not in self._device_ids or device_id == self._displayed_device_id:
            return
        self._pinch_widgets[self._displayed_device_id].setVisible(False)
        self._pinch_widgets[device_id].setVisible(True)
        self._displayed_device_id = device_id

    def update(self, device_id: int):
        """Called via _GUIBridge signal on every new-data frame."""
        if device_id != self._displayed_device_id:
            return

        title = f"R1 GUI - Device {device_id}"
        if title != self._last_title:
            self.setWindowTitle(title)
            self._last_title = title

        exo_poss, _ = SG_main.get_exo_joints_poss_rots(device_id)
        self._gui_3d.update_hand_exo(exo_poss)

        tip_pos, tip_rot = SG_main.get_fingertips_pos_rot(device_id)
        self._gui_3d.set_fingertip_points(tip_pos, tip_rot)

        thimble_dims = SG_main.get_fingertip_thimble_dims(device_id)
        self._gui_3d.set_fingertip_thimbles(thimble_dims)

# ---------------------------------------------------------------------------
class R1RHM:
    """Creates one RobotHandMapper per device and optionally the 3D + pinch GUI window."""
    def __init__(self, device_ids: list[int], display_gui: bool, node: Node):
        self._device_ids = list(device_ids)
        self._current_assignments: dict[int, str] = {}
        self._gui = None
        self._bridge = None

        for device_id in device_ids:
            mapper = SG_main.create_robot_hand_mapper(device_id)
            default_config = _default_config_left if SG_main.get_handedness(device_id) == SG_T.Hand.LEFT else _default_config_right
            mapper.apply_config(default_config)
            self._current_assignments[device_id] = default_config.name

        if display_gui:
            self._gui = _RHMGUI(device_ids)
            self._bridge = _GUIBridge(self._gui)

        for device_id in device_ids:
            handedness_str = 'lh' if SG_main.get_handedness(device_id) == SG_T.Hand.LEFT else 'rh'
            node.create_service(
                SetRHMConfig,
                f'/r1/glove{device_id}/{handedness_str}/rhm_config',
                lambda req, res, did=device_id: self._set_rhm_config_callback(did, req, res),
            )

    def get_pinch_percentages(self, device_id: int) -> tuple:
        """Returns (flex_pinch, abd_pinch) from the RobotHandMapper."""
        return SG_main.get_rhm_percentage_bents(device_id)

    def apply_config(self, device_id: int, config_name: str) -> bool:
        """Assign a named config to a device at runtime. Returns False if unknown."""
        if device_id not in self._device_ids:
            return False
        config = CONFIGS.get(config_name)
        if config is None:
            return False
        SG_main.get_robot_hand_mapper(device_id).apply_config(config)
        self._current_assignments[device_id] = config_name
        return True

    def _set_rhm_config_callback(self, device_id: int, request: SetRHMConfig.Request, response: SetRHMConfig.Response):
        response.available_configs = list(CONFIGS.keys())
        response.current_config = self._current_assignments.get(device_id, '')

        if not request.config_name:
            response.success = True
            response.message = f"Current config for device {device_id}: {response.current_config}"
            return response

        ok = self.apply_config(device_id, request.config_name)
        if ok:
            response.success = True
            response.message = f"Assigned '{request.config_name}' to device {device_id}."
        else:
            response.success = False
            response.message = f"Unknown config '{request.config_name}'."
        response.current_config = self._current_assignments.get(device_id, '')
        return response

    def set_displayed_device(self, device_id: int):
        """Switch which device's data is shown in the GUI (thread-safe)."""
        if self._bridge is not None:
            self._bridge.switch_device_signal.emit(device_id)

    def update_gui(self, device_id: int):
        """Push latest data to pinch widget and 3D exo display."""
        if self._gui is None or device_id != self._gui._displayed_device_id:
            return
        SG_main.update_robot_hand_mapper_gui(device_id)
        self._bridge.update_signal.emit(device_id)

    def close(self):
        if self._gui is not None:
            self._gui.close()