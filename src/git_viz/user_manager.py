from pathlib import Path
import yaml
from typing import Dict, Optional, List
import shutil
from platformdirs import user_config_dir, user_data_dir
import hashlib
from PIL import Image
import os

class UserManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        """Initialize UserManager with optional custom config and data directories.
        
        Args:
            config_dir: Optional custom config directory. If None, uses platformdirs.
            data_dir: Optional custom data directory. If None, uses platformdirs.
        """
        if (config_dir is not None or data_dir is not None) and self._initialized:
            self._initialized = False
            
        if not self._initialized:
            self.app_name = "git-viz"
            
            # Set config directory
            if config_dir is not None:
                self.config_dir = Path(config_dir)
            else:
                self.config_dir = Path(user_config_dir(self.app_name))
                
            # Set data directory
            if data_dir is not None:
                self.data_dir = Path(data_dir)
            else:
                self.data_dir = Path(user_data_dir(self.app_name))
                
            self.avatar_dir = self.data_dir / "avatars"
            self.config_file = self.config_dir / "users.yaml"
            
            # Create necessary directories
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.avatar_dir.mkdir(parents=True, exist_ok=True)
            
            # Load or create user mappings
            self._load_user_mappings()
            self._initialized = True

    def _load_user_mappings(self) -> None:
        """Load user mappings from config file or create default."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.user_mappings = yaml.safe_load(f) or {}
        else:
            self.user_mappings = {}
            self._save_user_mappings()

    def _save_user_mappings(self) -> None:
        """Save user mappings to config file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.user_mappings, f)

    @classmethod
    def reset(cls):
        """Reset the singleton instance for testing purposes."""
        cls._instance = None

    def add_user_mapping(self, git_name: str, canonical_name: str) -> None:
        """Add a mapping between a Git username and canonical name."""
        if git_name not in self.user_mappings:
            self.user_mappings[git_name] = {
                'canonical_name': canonical_name,
                'avatar': None
            }
        else:
            self.user_mappings[git_name]['canonical_name'] = canonical_name
        self._save_user_mappings()

    def get_canonical_name(self, git_name: str) -> str:
        """Get the canonical name for a Git username."""
        if git_name in self.user_mappings:
            return self.user_mappings[git_name]['canonical_name']
        return git_name

    def set_user_avatar(self, canonical_name: str, avatar_path: Path) -> None:
        """Set an avatar for a user and process it for Gource."""
        if not avatar_path.exists():
            raise FileNotFoundError(f"Avatar file not found: {avatar_path}")

        # Generate a unique filename based on the canonical name
        avatar_hash = hashlib.md5(canonical_name.encode()).hexdigest()
        new_avatar_path = self.avatar_dir / f"{avatar_hash}.png"

        # Process and save the avatar
        with Image.open(avatar_path) as img:
            # Resize to Gource's preferred size (maintaining aspect ratio)
            max_size = (128, 128)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create a square image with padding if necessary
            square_size = max(img.size)
            new_img = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
            paste_pos = ((square_size - img.size[0]) // 2,
                        (square_size - img.size[1]) // 2)
            new_img.paste(img, paste_pos)
            
            # Save the processed avatar
            new_img.save(new_avatar_path, 'PNG')

        # Update user mappings
        for user_data in self.user_mappings.values():
            if user_data['canonical_name'] == canonical_name:
                user_data['avatar'] = str(new_avatar_path)
        self._save_user_mappings()

    def get_avatar_dir(self) -> Path:
        """Get the directory containing user avatars."""
        return self.avatar_dir

    def get_all_users(self) -> Dict[str, Dict]:
        """Get all user mappings."""
        return self.user_mappings

    def suggest_similar_users(self, git_name: str) -> List[str]:
        """Suggest similar usernames based on string similarity."""
        from difflib import SequenceMatcher

        def similarity(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        similar_users = []
        for existing_name in self.user_mappings.keys():
            if similarity(git_name, existing_name) > 0.6:  # Threshold for similarity
                similar_users.append(existing_name)

        return similar_users
