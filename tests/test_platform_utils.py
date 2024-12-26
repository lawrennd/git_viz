import pytest
import platform
import subprocess
from pathlib import Path
import tempfile
import os
from git_viz.platform_utils import (
    get_platform_specific_path,
    check_dependencies,
    run_command,
    convert_to_timestamp,
    ensure_directory
)

def test_get_platform_specific_path():
    """Test platform-specific path conversion."""
    test_path = "dir1/dir2/file.txt"
    result = get_platform_specific_path(test_path)
    
    if platform.system() == 'Windows':
        assert str(result) == "dir1\\dir2\\file.txt"
    else:
        assert str(result) == "dir1/dir2/file.txt"

def test_check_dependencies():
    """Test dependency checking."""
    missing = check_dependencies()
    assert isinstance(missing, list)
    # Note: Test might need to be skipped if dependencies are actually missing
    if not missing:
        pytest.skip("Dependencies not available")

def test_run_command_success():
    """Test successful command execution."""
    if platform.system() == 'Windows':
        result = run_command(['cmd', '/c', 'echo', 'test'])
    else:
        result = run_command(['echo', 'test'])
    
    assert result.returncode == 0

def test_run_command_failure():
    """Test handling of failed commands."""
    with pytest.raises(RuntimeError):
        run_command(['nonexistent_command'])

def test_run_command_with_output():
    """Test command execution with output capture."""
    if platform.system() == 'Windows':
        result = run_command(
            ['cmd', '/c', 'echo', 'test'],
            stdout=subprocess.PIPE
        )
    else:
        result = run_command(
            ['echo', 'test'],
            stdout=subprocess.PIPE
        )
    
    assert result.stdout is not None
    assert b'test' in result.stdout

@pytest.mark.parametrize("test_date,expected", [
    ("2023-01-01", 1672531200),  # Timestamp for 2023-01-01 00:00:00 UTC
    ("2000-01-01", 946684800),   # Timestamp for 2000-01-01 00:00:00 UTC
])
def test_convert_to_timestamp(test_date, expected):
    """Test date string to timestamp conversion."""
    result = convert_to_timestamp(test_date)
    assert abs(result - expected) < 86400  # Allow for timezone differences

def test_convert_to_timestamp_invalid():
    """Test handling of invalid date formats."""
    with pytest.raises(ValueError):
        convert_to_timestamp("invalid-date")
    
    with pytest.raises(ValueError):
        convert_to_timestamp("2023/01/01")

def test_ensure_directory():
    """Test directory creation and verification."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir" / "nested_dir"
        
        # Create directory
        result = ensure_directory(test_dir)
        
        assert result.exists()
        assert result.is_dir()
        assert str(result) == str(test_dir)
        
        # Test idempotency
        result2 = ensure_directory(test_dir)
        assert result2.exists()
        assert result == result2

def test_ensure_directory_with_file():
    """Test handling of path that exists as file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test_file"
        test_file.write_text("test")
        
        with pytest.raises(OSError):
            ensure_directory(test_file)

@pytest.mark.skipif(platform.system() != 'Windows',
                    reason="Windows-specific test")
def test_windows_specific_command():
    """Test Windows-specific command handling."""
    result = run_command(['cmd', '/c', 'echo', 'test'], stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert b'test' in result.stdout

@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="Unix-specific test")
def test_unix_specific_command():
    """Test Unix-specific command handling."""
    result = run_command(['echo', 'test'], stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert b'test' in result.stdout