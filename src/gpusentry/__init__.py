"""GPUSentry - GPU monitoring and intelligent reporting system."""

from . import board, backend
from .database import DatabaseManager, GPUStat

__version__ = "1.0.1"
__author__ = "xiyuanyang-code"
__all__ = [
    'board',
    'backend',
    'DatabaseManager',
    'GPUStat',
]