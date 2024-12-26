"""Test suite for git-viz package."""
import pytest
import tempfile
import os
from pathlib import Path
import shutil
from contextlib import contextmanager

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data that persists across all tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_image(test_data_dir):
    """Create a sample image for avatar testing."""
    from PIL import Image
    
    image_path = test_data_dir / "sample_avatar.png"
    img = Image.new('RGB', (200, 200), color='red')
    img.save(image_path)
    return image_path

@contextmanager
def create_git_repo():
    """Create a temporary Git repository with some sample commits."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Initialize git repo
        os.chdir(repo_dir)
        os.system("git init")
        
        # Configure git user
        os.system('git config user.email "test@example.com"')
        os.system('git config user.name "Test User"')
        
        # Create some test files and commits
        for i in range(3):
            file_path = repo_dir / f"file{i}.txt"
            file_path.write_text(f"Content {i}")
            os.system(f"git add {file_path}")
            os.system(f'git commit -m "Add file {i}"')
        
        yield repo_dir

@pytest.fixture
def git_repo():
    """Fixture that provides a temporary Git repository."""
    with create_git_repo() as repo:
        yield repo

@pytest.fixture
def clean_env():
    """Fixture to provide a clean environment by temporarily clearing certain env vars."""
    # Save current environment variables
    saved_vars = {}
    vars_to_clear = ['GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL', 
                     'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL']
    
    for var in vars_to_clear:
        if var in os.environ:
            saved_vars[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore environment variables
    for var, value in saved_vars.items():
        os.environ[var] = value

@pytest.fixture
def mock_dependencies(monkeypatch):
    """Mock external dependencies for testing."""
    def mock_which(cmd):
        return f"/usr/bin/{cmd}"
    
    monkeypatch.setattr(shutil, 'which', mock_which)
    yield

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "requires_gource: mark test as requiring Gource installation"
    )
    config.addinivalue_line(
        "markers",
        "requires_ffmpeg: mark test as requiring FFmpeg installation"
    )

def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless explicitly requested."""
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    skip_gource = pytest.mark.skip(reason="Gource not available")
    skip_ffmpeg = pytest.mark.skip(reason="FFmpeg not available")
    
    # Check if integration tests should run
    run_integration = config.getoption("--integration", default=False)
    
    # Check if required tools are available
    has_gource = shutil.which('gource') is not None
    has_ffmpeg = shutil.which('ffmpeg') is not None
    
    for item in items:
        # Skip integration tests if not explicitly requested
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)
        
        # Skip tests requiring Gource if not available
        if "requires_gource" in item.keywords and not has_gource:
            item.add_marker(skip_gource)
        
        # Skip tests requiring FFmpeg if not available
        if "requires_ffmpeg" in item.keywords and not has_ffmpeg:
            item.add_marker(skip_ffmpeg)

def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )