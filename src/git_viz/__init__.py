"""
git_viz - Git repository visualization tool with user management
"""
from importlib import metadata

try:
    __version__ = metadata.version("git-viz")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

from .core import GitVizProcessor
from .user_manager import UserManager
from .platform_utils import (
    check_dependencies,
    get_platform_specific_path,
    convert_to_timestamp,
    ensure_directory,
)

__all__ = [
    "GitVizProcessor",
    "UserManager",
    "check_dependencies",
    "get_platform_specific_path",
    "convert_to_timestamp",
    "ensure_directory",
]