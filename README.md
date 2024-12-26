# Git-Viz: Your Git History Visualizer

Git-Viz is a powerful tool for creating beautiful visualizations of Git repository activity, perfect for creating year-in-review summaries, project presentations, or tracking team collaboration patterns. Built with cross-platform support and user management in mind.

## 🌟 Features

- Create engaging video visualizations of Git repository activity
- Manage and unify different Git usernames for the same contributor
- Support for custom user avatars
- Cross-platform compatibility (Windows, macOS, Linux)
- Create year-in-review summaries of Git activity
- Handle multiple repositories simultaneously
- Customizable visualization settings

## 📋 Prerequisites

- Python 3.8 or higher
- [Gource](https://gource.io/)
- FFmpeg

### Installing Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install gource ffmpeg
```

#### macOS
```bash
brew install gource ffmpeg
```

#### Windows
```bash
choco install gource ffmpeg
```

## 🚀 Installation

Install using pip:
```bash
pip install git-viz
```

Or with Poetry:
```bash
poetry add git-viz
```

## 🎥 Quick Start: Year in Review

Create your own Git activity year-in-review visualization in minutes:

```bash
# 1. First, set up your user mappings (if you use different emails/names)
git-viz users map "john.doe@work.com" "John Doe"
git-viz users map "johnd@personal.com" "John Doe"

# 2. Add a custom avatar (optional)
git-viz users set-avatar "John Doe" path/to/avatar.png

# 3. Generate your year in review
git-viz visualize \
    --start-date 2023-01-01 \
    --end-date 2023-12-31 \
    --output year2023.mp4 \
    ~/projects/repo1 ~/projects/repo2 ~/work/repos
```

This will create a cinematic visualization of your Git activity throughout the year!

## 🛠️ Advanced Usage

### User Management

```bash
# List all user mappings
git-viz users list

# Map multiple Git usernames to a canonical name
git-viz users map "john.work@company.com" "John Doe"
git-viz users map "john.personal@gmail.com" "John Doe"

# Set user avatar
git-viz users set-avatar "John Doe" ~/pictures/avatar.png
```

### Visualization Options

```bash
# Custom time scaling
git-viz visualize \
    --seconds-per-day 0.1 \
    --time-scale 2.0 \
    path/to/repos

# Focus on specific users
git-viz visualize \
    --highlight-users "John Doe,Jane Smith" \
    path/to/repos

# Custom visualization style
git-viz visualize \
    --background-color "000000" \
    --user-scale 6.0 \
    --font-size 25 \
    path/to/repos
```

### Python API

You can also use Git-Viz programmatically:

```python
from git_viz import GitVizProcessor, UserManager

# Set up user management
user_manager = UserManager()
user_manager.add_user_mapping("john.doe@work.com", "John Doe")
user_manager.set_user_avatar("John Doe", "path/to/avatar.png")

# Create visualization
with GitVizProcessor(
    start_date="2023-01-01",
    end_date="2023-12-31",
    output_file="year_review.mp4",
    user_manager=user_manager
) as processor:
    processor.process_repositories([
        "~/projects/repo1",
        "~/projects/repo2"
    ])
```

## 🎨 Creating a Year in Review

Here's a complete guide to creating an engaging year-in-review visualization:

1. **Prepare Your Repositories**
   ```bash
   # Create a directory for your repos
   mkdir ~/git-year-review
   cd ~/git-year-review
   
   # Clone all repositories you want to include
   git clone https://github.com/user/repo1.git
   git clone https://github.com/user/repo2.git
   ```

2. **Set Up User Identity**
   ```bash
   # Map all your different Git identities
   git-viz users map "work.email@company.com" "Your Name"
   git-viz users map "personal@gmail.com" "Your Name"
   
   # Add your avatar
   git-viz users set-avatar "Your Name" ~/path/to/avatar.png
   ```

3. **Generate the Visualization**
   ```bash
   git-viz visualize \
       --start-date 2023-01-01 \
       --end-date 2023-12-31 \
       --seconds-per-day 0.5 \
       --highlight-users "Your Name" \
       --time-scale 2.0 \
       --output year2023.mp4 \
       ~/git-year-review/*
   ```

4. **Customize the Output**
   - Adjust `--seconds-per-day` to control visualization speed
   - Use `--highlight-users` to focus on specific team members
   - Modify `--user-scale` to adjust user avatar size
   - Change `--background-color` for different aesthetics

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Install development dependencies:
   ```bash
   poetry install
   ```
4. Make your changes and add tests
5. Run tests:
   ```bash
   poetry run pytest
   ```
6. Commit your changes
7. Push to the branch
8. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the amazing [Gource](https://gource.io/) visualization engine
- Inspired by year-in-review features from services like Spotify and Strava
- Thanks to all contributors and users of the project

