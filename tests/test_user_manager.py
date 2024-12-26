import pytest
from pathlib import Path
import tempfile
import shutil
from git_viz.user_manager import UserManager

@pytest.fixture
def temp_dirs():
    """Create temporary directories for config and data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_dir = temp_path / "config"
        data_dir = temp_path / "data"
        
        # Create directories
        config_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        
        yield config_dir, data_dir

@pytest.fixture
def user_manager(temp_dirs):
    """Create a UserManager instance with temporary directories."""
    config_dir, data_dir = temp_dirs
    return UserManager(config_dir=config_dir, data_dir=data_dir)

def test_user_mapping(user_manager):
    """Test basic user mapping functionality."""
    # Test adding a mapping
    user_manager.add_user_mapping("john.doe", "John Doe")
    assert user_manager.get_canonical_name("john.doe") == "John Doe"
    
    # Test unknown user returns original name
    assert user_manager.get_canonical_name("unknown.user") == "unknown.user"

def test_user_suggestions(user_manager):
    """Test similar user suggestions."""
    # Add some test users
    user_manager.add_user_mapping("john.doe", "John Doe")
    user_manager.add_user_mapping("jane.doe", "Jane Doe")
    user_manager.add_user_mapping("bob.smith", "Bob Smith")
    
    # Test similar name suggestions
    similar = user_manager.suggest_similar_users("john.d")
    assert "john.doe" in similar
    assert "bob.smith" not in similar

@pytest.mark.skipif(not shutil.which('convert'), 
                    reason="ImageMagick not available")
def test_avatar_processing(user_manager, tmp_path):
    """Test avatar processing functionality."""
    # Create a test image
    from PIL import Image
    test_image = tmp_path / "test_avatar.png"
    img = Image.new('RGB', (200, 200), color='red')
    img.save(test_image)
    
    # Test setting avatar
    user_manager.add_user_mapping("john.doe", "John Doe")
    user_manager.set_user_avatar("John Doe", test_image)
    
    # Verify avatar was processed and saved
    user_data = user_manager.get_all_users()["john.doe"]
    assert user_data["avatar"] is not None
    assert Path(user_data["avatar"]).exists()
    
    # Verify avatar dimensions
    with Image.open(user_data["avatar"]) as avatar:
        assert avatar.size[0] <= 128
        assert avatar.size[1] <= 128

def test_persistence(temp_dirs):
    """Test that user mappings persist between instances."""
    config_dir, data_dir = temp_dirs
    
    # Create first instance and add mapping
    manager1 = UserManager(config_dir=config_dir, data_dir=data_dir)
    manager1.add_user_mapping("john.doe", "John Doe")
    
    # Create second instance and verify mapping exists
    manager2 = UserManager(config_dir=config_dir, data_dir=data_dir)
    assert manager2.get_canonical_name("john.doe") == "John Doe"

def test_invalid_avatar_path(user_manager):
    """Test handling of invalid avatar paths."""
    user_manager.add_user_mapping("john.doe", "John Doe")
    
    with pytest.raises(FileNotFoundError):
        user_manager.set_user_avatar("John Doe", Path("nonexistent.png"))

def test_custom_directories(temp_dirs):
    """Test that custom directory paths are respected."""
    config_dir, data_dir = temp_dirs
    
    manager = UserManager(config_dir=config_dir, data_dir=data_dir)
    
    # Verify directories were created
    assert config_dir.exists()
    assert data_dir.exists()
    assert (data_dir / "avatars").exists()
    
    # Verify config file location
    assert manager.config_file.parent == config_dir
    
    # Test functionality with custom directories
    manager.add_user_mapping("test.user", "Test User")
    assert (config_dir / "users.yaml").exists()

def test_singleton_with_different_dirs(temp_dirs):
    """Test that singleton properly reinitializes with new directories."""
    config_dir1, data_dir1 = temp_dirs
    config_dir2 = config_dir1 / "other_config"
    data_dir2 = data_dir1 / "other_data"
    
    # First initialization
    manager1 = UserManager(config_dir=config_dir1, data_dir=data_dir1)
    assert (data_dir1 / "avatars").exists()
    
    # Second initialization with different dirs
    manager2 = UserManager(config_dir=config_dir2, data_dir=data_dir2)
    assert (data_dir2 / "avatars").exists()
    
    # Verify it's the same instance but with updated paths
    assert manager1 is manager2
    assert manager2.data_dir == data_dir2