"""
Tracks which SG_API release r1_ros has been validated against.
"""
import importlib.metadata

SUPPORTED_SG_API_VERSION = "0.1"


def get_installed_sg_api_version() -> str:
    """Version of the SG_API distribution currently installed."""
    return importlib.metadata.version("SG_API")


def is_sg_api_version_supported() -> bool:
    """True if the installed SG_API version matches the pinned version."""
    return get_installed_sg_api_version() == SUPPORTED_SG_API_VERSION
