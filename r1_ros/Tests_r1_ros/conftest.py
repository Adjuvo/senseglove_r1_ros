"""
Shared pytest fixtures for r1_ros's SG_API-adapter tests.
"""
import pytest

from SG_API import SG_main, SG_types as SG_T
from SG_API import SG_simulator as SG_sim
from SG_API import SG_callback_manager as SG_cb
from SG_API import SG_timer


@pytest.fixture
def sim_device_id():
    """Boots one SIMULATED_GLOVE device (STEADY_MODE, filter off) and returns its device_id."""
    device_ids = SG_main.init(
        1, SG_T.Com_type.SIMULATED_GLOVE, SG_sim.Simulation_Mode.STEADY_MODE
    )
    assert device_ids == [9999], (
        f"Expected SG_main.init(1, SIMULATED_GLOVE, ...) to create exactly "
        f"one device at the hard-coded id 9999 (see "
        f"SG_main.init_rembrandt_sim), got {device_ids}. If SG_API's "
        f"device-id allocation changed, these tests' fixed-id assumption "
        f"needs revisiting."
    )
    device_id = device_ids[0]
    SG_main.set_filter(device_id, SG_T.Filter_type.OFF, 0.0)

    try:
        yield device_id
    finally:
        # Mirrors SG_API's clean_state_before_test teardown ordering.
        SG_timer.stop_timer(SG_cb._high_freq_timer_id)
        SG_main.exit()


class _StubR1Manager:
    """Duck-typed stand-in for R1Manager - just enough for _build_state_msg's self.get_clock()."""

    def get_clock(self):
        from rclpy.clock import Clock
        return Clock()


@pytest.fixture
def stub_r1_manager():
    return _StubR1Manager()
