from datetime import datetime
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tempfile
import shutil

from .platform_utils import get_platform_specific_path, run_command
from .user_manager import UserManager

class GitVizProcessor:
    def __init__(
        self,
        start_date: str = "2000-01-01",
        end_date: Optional[str] = None,
        output_file: str = "git-visualization.mp4",
        user_manager: Optional[UserManager] = None,
    ):
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.output_file = output_file
        self.user_manager = user_manager or UserManager()
        self.temp_dir = Path(tempfile.mkdtemp())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.temp_dir)

    def _generate_gource_log(self, repo_path: Path) -> Path:
        """Generate a Gource log file for a single repository."""
        log_file = self.temp_dir / f"{repo_path.name}.log"
        run_command(["gource", "--output-custom-log", str(log_file), str(repo_path)])
        return log_file

    def _filter_log_by_date(self, log_file: Path, repo_name: str) -> Path:
        """Filter log file by date range and augment with repository name."""
        filtered_log = self.temp_dir / f"{log_file.stem}.filtered.log"
        
        start_timestamp = int(datetime.strptime(self.start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(self.end_date, "%Y-%m-%d").timestamp())
        
        with open(log_file, 'r') as f_in, open(filtered_log, 'w') as f_out:
            for line in f_in:
                timestamp, user, action, path = line.strip().split('|')
                if start_timestamp <= int(float(timestamp)) <= end_timestamp:
                    # Map the user to their canonical name
                    canonical_user = self.user_manager.get_canonical_name(user)
                    f_out.write(f"{timestamp}|{canonical_user}|{action}|{repo_name}/{path}\n")
        
        return filtered_log

    def process_repositories(self, directories: List[str]) -> None:
        """Process multiple Git repositories and generate a combined visualization."""
        all_logs = []

        # Process each repository
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                print(f"Warning: Directory {directory} does not exist.")
                continue

            for git_dir in dir_path.rglob('.git'):
                repo_path = git_dir.parent
                print(f"Processing repository: {repo_path}")
                
                # Generate and filter log
                log_file = self._generate_gource_log(repo_path)
                filtered_log = self._filter_log_by_date(log_file, repo_path.name)
                all_logs.append(filtered_log)

        # Combine all logs
        combined_log = self.temp_dir / "combined.log"
        with open(combined_log, 'w') as outfile:
            for log_file in all_logs:
                with open(log_file, 'r') as infile:
                    outfile.write(infile.read())

        # Generate final visualization
        self._generate_visualization(combined_log)

    def _generate_visualization(self, combined_log: Path) -> None:
        """Generate the final visualization using Gource and FFmpeg."""
        gource_cmd = [
            "gource",
            str(combined_log),
            "--seconds-per-day", "0.5",
            "--auto-skip-seconds", ".3",
            "--multi-sampling",
            "--stop-at-end",
            "--background-colour", "000000",
            "--font-size", "25",
            "--user-scale", "6.0",
            "--user-image-dir", str(self.user_manager.get_avatar_dir()),
            "--user-font-size", "30",
            "--output-framerate", "60",
            "--output-ppm-stream", "-"
        ]

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "image2pipe",
            "-framerate", "60",
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-movflags", "+faststart",
            self.output_file
        ]

        # Run Gource and pipe to FFmpeg
        gource_process = subprocess.Popen(
            gource_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd, stdin=gource_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Close gource's stdout to signal EOF to ffmpeg
        gource_process.stdout.close()
        
        # Wait for completion
        ffmpeg_process.communicate()

        if ffmpeg_process.returncode != 0:
            raise RuntimeError("Failed to generate visualization")