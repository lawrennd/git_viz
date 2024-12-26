import pytest
from pathlib import Path
import tempfile
import shutil
from git_viz.user_manager import UserManager

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        old_config_dir = UserManager.config_dir
        old_data_dir = UserManager.data_dir
        
        # Patch the config and data directories
        UserManager.config_dir = Path(temp_dir) / "config"
        UserManager.data_dir = Path(temp_dir) / "data"
        
        yield temp_dir
        
        # Restore original paths
        UserManager.config_dir = old_config_dir
        UserManager.data_dir = old_data_dir

def test_user_mapping(temp_config_dir):
    """Test basic user mapping functionality."""
    manager = UserManager()
    
    # Test adding a mapping
    manager.add_user_mapping("john.doe", "John Doe")
    assert manager.get_canonical_name("john.doe") == "John Doe"
    
    # Test unknown user returns original name
    assert manager.get_canonical_name("unknown.user") == "unknown.user"

def test_user_suggestions(temp_config_dir):
    """Test similar user suggestions."""
    manager = UserManager()
    
    # Add some test users
    manager.add_user_mapping("john.doe", "John Doe")
    manager.add_user_mapping("jane.doe", "Jane Doe")
    manager.add_user_mapping("bob.smith", "Bob Smith")
    
    # Test similar name suggestions
    similar = manager.suggest_similar_users("john.d")
    assert "john.doe" in similar
    assert "bob.smith" not in similar

@pytest.mark.skipif(not shutil.which('convert'), 
                    reason="ImageMagick not available")
def test_avatar_processing(temp_config_dir):
    """Test avatar processing functionality."""
    manager = UserManager()
    
    # Create a test image
    from PIL import Image
    test_image = Path(temp_config_dir) / "test_avatar.png"
    img = Image.new('RGB', (200, 200), color='red')
    img.save(test_image)
    
    # Test setting avatar
    manager.add_user_mapping("john.doe", "John Doe")
    manager.set_user_avatar("John Doe", test_image)
    
    # Verify avatar was processed and saved
    user_data = manager.get_all_users()["john.doe"]
    assert user_data["avatar"] is not None
    assert Path(user_data["avatar"]).exists()
    
    # Verify avatar dimensions
    with Image.open(user_data["avatar"]) as avatar:
        assert avatar.size[0] <= 128
        assert avatar.size[1] <= 128

def test_persistence(temp_config_dir):
    """Test that user mappings persist between instances."""
    # Create first instance and add mapping
    manager1 = UserManager()
    manager1.add_user_mapping("john.doe", "John Doe")
    
    # Create second instance and verify mapping exists
    manager2 = UserManager()
    assert manager2.get_canonical_name("john.doe") == "John Doe"

def test_invalid_avatar_path(temp_config_dir):
    """Test handling of invalid avatar paths."""
    manager = UserManager()
    manager.add_user_mapping("john.doe", "John Doe")
    
    with pytest.raises(FileNotFoundError):
        manager.set_user_avatar("John Doe", Path("nonexistent.png"))