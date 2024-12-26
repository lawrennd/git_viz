import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
from git_viz.cli import cli
from git_viz.user_manager import UserManager

import os

@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()

@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository for testing."""
    original_dir = os.getcwd()  # Store original directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / "test_repo"
        repo_dir.mkdir()
        
        # Initialize git repo
        os.chdir(repo_dir)
        os.system("git init")
        os.system('git config user.email "test@example.com"')
        os.system('git config user.name "Test User"')
        
        # Create a test file and commit it
        test_file = repo_dir / "test.txt"
        test_file.write_text("Test content")
        os.system("git add test.txt")
        os.system('git commit -m "Initial commit"')
        
        yield repo_dir
        
        # Restore original directory
        os.chdir(original_dir)

def test_cli_version(runner):
    """Test the --version flag."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "git-viz" in result.output

def test_visualize_command_no_args(runner):
    """Test visualize command with no arguments."""
    result = runner.invoke(cli, ["visualize"])
    assert result.exit_code != 0
    assert "Error: Please specify at least one directory" in result.output

def test_visualize_command_invalid_path(runner):
    """Test visualize command with invalid path."""
    result = runner.invoke(cli, ["visualize", "/nonexistent/path"])
    assert result.exit_code != 0

def test_visualize_command_valid_path(runner, temp_git_repo, mocker):
    """Test visualize command logic with valid repository path."""
    # Mock all external dependencies
    mocker.patch('git_viz.cli.check_dependencies', return_value=[])
    mocker.patch('git_viz.core.run_command')  # Mock the run_command function
    mocker.patch('subprocess.Popen')  # Mock subprocess calls
    
    mock_processor = mocker.MagicMock()
    mock_processor_cls = mocker.patch('git_viz.cli.GitVizProcessor')
    mock_processor_cls.return_value.__enter__.return_value = mock_processor

    with runner.isolated_filesystem():
        result = runner.invoke(cli, [
            "visualize",
            str(temp_git_repo),
            "--output", "test_output.mp4"
        ])
        
        assert result.exit_code == 0
        
        # Assert GitVizProcessor was created with correct parameters
        mock_processor_cls.assert_called_once_with(
            start_date='2000-01-01',
            end_date=None,
            output_file='test_output.mp4'
        )
        
        # Assert process_repositories was called with the correct path
        mock_processor.process_repositories.assert_called_once_with([str(temp_git_repo)])

def test_users_map_command(runner):
    """Test user mapping command."""
    with runner.isolated_filesystem():
        # Simulate user input 'y' for the confirmation prompt
        result = runner.invoke(cli, [
            "users", "map",
            "test.user", "Test User"
        ], input='y\n')  # Add this input parameter
        
        assert result.exit_code == 0
        assert "Mapped 'test.user' to 'Test User'" in result.output

def test_users_map_similar_names(runner):
    """Test user mapping with similar existing names."""
    with runner.isolated_filesystem():
        # First mapping
        runner.invoke(cli, ["users", "map", "john.doe", "John Doe"])
        
        # Try similar name
        result = runner.invoke(cli, ["users", "map", "john.d", "John D"], input="n\n")
        assert result.exit_code == 0
        assert "Similar existing usernames found" in result.output

def test_users_set_avatar_invalid_path(runner):
    """Test setting avatar with invalid path."""
    result = runner.invoke(cli, [
        "users", "set-avatar",
        "Test User", "/nonexistent/avatar.png"
    ])
    assert result.exit_code != 0
    assert "Error" in result.output

def test_users_set_avatar_valid_path(runner):
    """Test setting avatar with valid path."""
    with runner.isolated_filesystem():
        # Create a test image
        from PIL import Image
        avatar_path = Path("test_avatar.png")
        img = Image.new('RGB', (100, 100), color='red')
        img.save(avatar_path)
        
        # Map user first
        runner.invoke(cli, ["users", "map", "test.user", "Test User"])
        
        # Set avatar
        result = runner.invoke(cli, [
            "users", "set-avatar",
            "Test User", str(avatar_path)
        ])
        assert result.exit_code == 0
        assert "Avatar set for user" in result.output

def test_users_list_command(runner):
    """Test listing users command."""
    with runner.isolated_filesystem():
        # Add some test users
        runner.invoke(cli, ["users", "map", "john.doe", "John Doe"])
        runner.invoke(cli, ["users", "map", "jane.doe", "Jane Doe"])
        
        # List users
        result = runner.invoke(cli, ["users", "list"])
        assert result.exit_code == 0
        assert "john.doe -> John Doe" in result.output
        assert "jane.doe -> Jane Doe" in result.output


@pytest.fixture(autouse=True)
def clean_user_mappings(mocker):
    """Clean up user mappings before each test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Mock both config and data directories
        mocker.patch('platformdirs.user_config_dir', return_value=temp_path)
        mocker.patch('platformdirs.user_data_dir', return_value=temp_path)
        # Ensure the UserManager is reinitialized with empty mappings
        mocker.patch('git_viz.cli.user_manager._instance', None)
        yield

def test_users_list_empty(runner, mocker):
    """Test listing users when none exist."""
    # Create a mock user manager instance
    mock_user_manager = UserManager()
    mock_user_manager._mappings = {}
    # Mock the global user_manager instance in the cli module
    mocker.patch('git_viz.cli.user_manager', return_value=mock_user_manager)
    
    result = runner.invoke(cli, ["users", "list"])
    assert result.exit_code == 0
    assert "No user mappings found" in result.output
