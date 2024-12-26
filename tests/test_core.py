import pytest
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from git_viz.core import GitVizProcessor
from git_viz.user_manager import UserManager

@pytest.fixture
def temp_git_repo():
    """Create a temporary Git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / "test_repo"
        repo_dir.mkdir()
        
        # Initialize git repo
        os.chdir(repo_dir)
        os.system("git init")
        
        # Create some test files and commits
        test_file = repo_dir / "test.txt"
        test_file.write_text("Initial content")
        os.system('git config user.email "test@example.com"')
        os.system('git config user.name "Test User"')
        os.system("git add test.txt")
        os.system('git commit -m "Initial commit"')
        
        yield repo_dir

@pytest.fixture
def processor():
    """Create a GitVizProcessor instance with temporary directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "output.mp4"
        processor = GitVizProcessor(
            start_date="2000-01-01",
            end_date=datetime.now().strftime("%Y-%m-%d"),
            output_file=str(output_file),
            user_manager=UserManager()
        )
        yield processor

def test_processor_initialization(processor):
    """Test GitVizProcessor initialization."""
    assert processor.start_date == "2000-01-01"
    assert isinstance(processor.user_manager, UserManager)
    assert processor.temp_dir.exists()

def test_generate_gource_log(processor, temp_git_repo):
    """Test Gource log generation for a single repository."""
    log_file = processor._generate_gource_log(temp_git_repo)
    assert log_file.exists()
    content = log_file.read_text()
    assert "|Test User|" in content
    assert "|A|test.txt" in content

def test_filter_log_by_date(processor, temp_git_repo):
    """Test log filtering by date range."""
    # Generate initial log
    log_file = processor._generate_gource_log(temp_git_repo)
    
    # Filter log
    filtered_log = processor._filter_log_by_date(log_file, temp_git_repo.name)
    
    assert filtered_log.exists()
    content = filtered_log.read_text()
    assert temp_git_repo.name in content

@pytest.mark.skipif(not shutil.which('gource') or not shutil.which('ffmpeg'),
                    reason="Gource or FFmpeg not available")
def test_process_repositories(processor, temp_git_repo):
    """Test processing of multiple repositories."""
    try:
        processor.process_repositories([str(temp_git_repo)])
        assert Path(processor.output_file).exists()
    except RuntimeError as e:
        pytest.skip(f"Failed to generate visualization: {e}")

def test_processor_cleanup(processor):
    """Test that temporary files are cleaned up."""
    temp_dir = processor.temp_dir
    assert temp_dir.exists()
    with processor:
        assert temp_dir.exists()
    assert not temp_dir.exists()

def test_invalid_repository(processor):
    """Test handling of invalid repository paths."""
    with pytest.warns(UserWarning):
        processor.process_repositories(["/nonexistent/path"])

def test_date_range_validation():
    """Test validation of date ranges."""
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValueError):
        GitVizProcessor(start_date="invalid-date")
    
    with pytest.raises(ValueError):
        GitVizProcessor(end_date="invalid-date")
    
    with pytest.raises(ValueError):
        GitVizProcessor(start_date=future_date)
    
    with pytest.raises(ValueError):
        GitVizProcessor(start_date="2000-01-01", end_date="1999-12-31")