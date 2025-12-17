"""
Configuration module - Application settings and constants
"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Default configurations
DEFAULT_OSRM_URL = "http://router.project-osrm.org"

__all__ = [
    "BASE_DIR",
    "DEFAULT_OSRM_URL",
]
