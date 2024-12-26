from datetime import datetime
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tempfile
import shutil
import warnings

# Add this import at the top of the file with the other imports
from .platform_utils import get_platform_specific_path, run_command, convert_to_timestamp
from .user_manager import UserManager

class GitVizProcessor:
    def __init__(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_file: str = "git-visualization.mp4",
        user_manager: Optional[UserManager] = None,
        config_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize GitVizProcessor.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to current date)
            output_file: Path for the output video file
            user_manager: Optional UserManager instance
            config_dir: Optional config directory path
            data_dir: Optional data directory path
        """
        # Validate dates if provided
        if start_date or end_date:
            try:
                if start_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    if start_dt > datetime.now():
                        raise ValueError("Start date cannot be in the future")
            
                if end_date:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                if start_date and end_date and end_dt < start_dt:
                    raise ValueError("End date cannot be before start date")
            
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError("Dates must be in YYYY-MM-DD format")
                raise

        self.start_date = start_date
        self.end_date = end_date
        self.output_file = output_file
        self.user_manager = user_manager or UserManager(config_dir=config_dir, data_dir=data_dir)
        self.temp_dir = Path(tempfile.mkdtemp())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary files on exit."""
        shutil.rmtree(self.temp_dir)

    def _generate_gource_log(self, repo_path: Path) -> Path:
        """
        Generate a Gource log file for a single repository.
        
        Args:
            repo_path: Path to the Git repository
            
        Returns:
            Path to the generated log file
        """
        log_file = self.temp_dir / f"{repo_path.name}.log"
        run_command(["gource", "--output-custom-log", str(log_file), str(repo_path)])
        return log_file

    def _filter_log_by_date(self, log_file: Path, repo_name: str) -> Path:
        """Filter Gource log by date range."""
        filtered_log = self.temp_dir / f"{repo_name}_filtered.log"
        
        # If no date filtering is needed, return the original log
        if not self.start_date and not self.end_date:
            return log_file
        
        start_timestamp = convert_to_timestamp(self.start_date) if self.start_date else float('-inf')
        end_timestamp = convert_to_timestamp(self.end_date) if self.end_date else float('inf')
        
        # Add debug logging
        print(f"Debug: Filtering between {start_timestamp} and {end_timestamp}")
        
        with log_file.open('r') as input_file, filtered_log.open('w') as output_file:
            for line in input_file:
                try:
                    timestamp = float(line.split('|')[0])  # Change to float for more precise comparison
                    # Add debug logging
                    print(f"Debug: Checking timestamp {timestamp}")
                    if start_timestamp <= timestamp <= end_timestamp:
                        output_file.write(line)
                    else:
                        print(f"Debug: Timestamp {timestamp} outside range {start_timestamp}-{end_timestamp}")
                except (ValueError, IndexError) as e:
                    print(f"Debug: Error processing line: {line.strip()} - {str(e)}")
                    continue
        
        return filtered_log

    def _combine_logs(self, log_files: List[Path], output_file: Path) -> None:
        """
        Combine multiple Gource log files into a single file.

        Args:
            log_files: List of paths to log files to combine
            output_file: Path where the combined log will be written
        """
        with output_file.open('w') as outfile:
            for log_file in log_files:
                if log_file.exists():
                    with log_file.open('r') as infile:
                        outfile.write(infile.read())
                    
    def process_repositories(self, repository_paths: List[str]) -> None:
        """
        Process multiple Git repositories and generate visualization.

        Args:
            repository_paths: List of paths to Git repositories to process

        Raises:
            ValueError: If no repository paths are provided
        """
        if not repository_paths:
            raise ValueError("No repository paths provided")

        combined_log = self.temp_dir / "combined.log"
        valid_logs = []
        any_repos_attempted = False

        # Process each repository
        for repo_path in repository_paths:
            repo = Path(repo_path)
            if not repo.exists():
                warnings.warn(f"Directory {repo_path} does not exist.")
                continue

            any_repos_attempted = True
            try:
                # Generate and validate the log file
                log_file = self._generate_gource_log(repo)
                if log_file.exists() and log_file.stat().st_size > 0:
                    # Filter the log file by date if needed
                    filtered_log = self._filter_log_by_date(log_file, repo.name)
                    if filtered_log.exists() and filtered_log.stat().st_size > 0:
                        valid_logs.append(filtered_log)
            except Exception as e:
                warnings.warn(f"Error processing repository {repo_path}: {str(e)}")

        # Handle results
        if valid_logs:
            try:
                # Combine valid logs and generate visualization
                self._combine_logs(valid_logs, combined_log)
                if combined_log.exists() and combined_log.stat().st_size > 0:
                    self._generate_visualization(combined_log)
                else:
                    warnings.warn("Combined log file is empty or could not be created")
            except Exception as e:
                warnings.warn(f"Error during visualization generation: {str(e)}")
        elif any_repos_attempted:
            warnings.warn("No valid repository logs were generated")

    def _generate_visualization(self, combined_log: Path) -> None:
        """
        Generate the final visualization using Gource and FFmpeg.
        
        Args:
        combined_log: Path to the combined log file
        """


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

        # Ensure we're in a valid working directory before running the processes
        work_dir = combined_log.parent
        if not work_dir.exists():
            work_dir.mkdir(parents=True)

        # Run Gource with explicit working directory
        gource_process = subprocess.Popen(
            gource_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(work_dir) 
        )


        # Add error checking for Gource process
        gource_error = gource_process.stderr.read()
        if gource_process.poll() is not None and gource_process.returncode != 0:
            raise RuntimeError(f"Gource failed: {gource_error.decode()}")

        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd, stdin=gource_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Close gource's stdout to signal EOF to ffmpeg
        if gource_process.stdout:
            gource_process.stdout.close()

        # Wait for completion and capture output
        ffmpeg_output, ffmpeg_error = ffmpeg_process.communicate()
        gource_process.wait()

        # Check both process return codes
        if gource_process.returncode != 0:
            error_msg = gource_error.decode() if gource_error else "Unknown Gource error"
            raise RuntimeError(f"Failed to generate visualization (Gource): {error_msg}")
    
        if ffmpeg_process.returncode != 0:
            error_msg = ffmpeg_error.decode() if ffmpeg_error else "Unknown FFmpeg error"
            raise RuntimeError(f"Failed to generate visualization (FFmpeg): {error_msg}")        

    def get_repository_stats(self) -> Dict[str, Dict]:
        """
        Get statistics about processed repositories.
        
        Returns:
            Dictionary containing repository statistics
        """
        stats = {}
        for log_file in self.temp_dir.glob("*.filtered.log"):
            repo_stats = {
                'commits': 0,
                'users': set(),
                'files_modified': 0,
                'files_added': 0,
                'files_deleted': 0
            }
            
            with open(log_file, 'r') as f:
                for line in f:
                    _, user, action, _ = line.strip().split('|')
                    repo_stats['users'].add(user)
                    
                    if action == 'M':
                        repo_stats['files_modified'] += 1
                    elif action == 'A':
                        repo_stats['files_added'] += 1
                    elif action == 'D':
                        repo_stats['files_deleted'] += 1
                        
                    repo_stats['commits'] += 1
            
            repo_stats['users'] = list(repo_stats['users'])
            stats[log_file.stem.replace('.filtered', '')] = repo_stats
            
        return stats
    
