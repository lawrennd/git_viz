import platform
import subprocess
from pathlib import Path
from typing import List, Union, Optional
import shutil
import os

def get_platform_specific_path(path: Union[str, Path]) -> Path:
    """Convert a path to the platform-specific format."""
    return Path(str(path).replace('/', os.sep))

def check_dependencies() -> List[str]:
    """Check if required external dependencies are installed."""
    missing_deps = []
    
    # Check for Gource
    if not shutil.which('gource'):
        missing_deps.append('gource')
    
    # Check for FFmpeg
    if not shutil.which('ffmpeg'):
        missing_deps.append('ffmpeg')
    
    return missing_deps

def run_command(
    command: List[str],
    check: bool = True,
    stdout: Optional[int] = None,
    stderr: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """
    Run a command with platform-specific adjustments.
    
    Args:
        command: Command and arguments as list
        check: Whether to check return code
        stdout: Subprocess stdout option
        stderr: Subprocess stderr option
    
    Returns:
        CompletedProcess instance
    """
    # On Windows, ensure we use the correct executable names
    if platform.system() == 'Windows':
        if command[0] == 'gource':
            command[0] = 'gource.exe'
        elif command[0] == 'ffmpeg':
            command[0] = 'ffmpeg.exe'
    
    try:
        # Set creation flags for Windows to prevent console window
        creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        
        return subprocess.run(
            command,
            check=check,
            stdout=stdout,
            stderr=stderr,
            creationflags=creation_flags if platform.system() == 'Windows' else 0
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"Command not found: {command[0]}") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(command)}") from e

def get_timestamp_format() -> str:
    """Get the platform-specific timestamp format for date conversion."""
    if platform.system() == 'Darwin':  # macOS
        return "%Y-%m-%d"
    else:  # Linux and Windows
        return "%Y-%m-%d"

def convert_to_timestamp(date_str: str) -> int:
    """
    Convert a date string to Unix timestamp in a platform-independent way.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
    
    Returns:
        Unix timestamp as integer
    """
    import datetime
    
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD: {e}")

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists and create it if it doesn't.
    
    Args:
        path: Directory path
    
    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
