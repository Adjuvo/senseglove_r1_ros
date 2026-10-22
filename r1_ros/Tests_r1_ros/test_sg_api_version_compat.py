"""Guards against running r1_ros against an SG_API release it hasn't been validated against."""
from .compat import SUPPORTED_SG_API_VERSION, get_installed_sg_api_version


def test_installed_sg_api_version_matches_pin():
    installed = get_installed_sg_api_version()
    assert installed == SUPPORTED_SG_API_VERSION, (
        f"SG_API {installed} is installed, but r1_ros has only been "
        f"validated against SG_API {SUPPORTED_SG_API_VERSION}. If SG_API "
        f"was intentionally upgraded: re-run r1_ros's test suite against "
        f"it, then bump SUPPORTED_SG_API_VERSION in r1_ros/Tests_r1_ros/compat.py."
    )
