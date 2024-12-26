import click
from pathlib import Path
from typing import List, Optional
import sys

from .core import GitVizProcessor
from .user_manager import UserManager
from .platform_utils import check_dependencies

user_manager = UserManager()

@click.group()
@click.version_option(package_name="git-viz", message='%(package)s, version %(version)s') 
def cli():
    """Git repository visualization tool with user management."""
    pass

@cli.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True))
@click.option('--start-date', '-s', default='2000-01-01',
              help='Start date in YYYY-MM-DD format')
@click.option('--end-date', '-e', default=None,
              help='End date in YYYY-MM-DD format')
@click.option('--output', '-o', default='git-visualization.mp4',
              help='Output file path')
def visualize(directories, start_date: str, end_date: Optional[str],
              output: str):
    """Generate a visualization for the specified Git repositories."""
    # Check dependencies
    missing = check_dependencies()
    if missing:
        click.echo(f"Error: Missing required dependencies: {', '.join(missing)}")
        click.echo("Please install them before running this command.")
        sys.exit(1)
    
    if not directories:
        click.echo("Error: Please specify at least one directory containing Git repositories.")
        sys.exit(1)
    
    try:
        with GitVizProcessor(
            start_date=start_date,
            end_date=end_date,
            output_file=output
        ) as processor:
            # Convert directories tuple to list before passing
            processor.process_repositories([str(d) for d in directories])
        click.echo(f"Visualization saved to: {output}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@cli.group()
def users():
    """Manage user mappings and avatars."""
    pass

@users.command()
@click.argument('git-name')
@click.argument('canonical-name')
def map(git_name: str, canonical_name: str):
    """Map a Git username to a canonical name."""
    user_manager = UserManager()
    
    # Check for similar existing users
    similar = user_manager.suggest_similar_users(git_name)
    if similar:
        click.echo("Note: Similar existing usernames found:")
        for name in similar:
            click.echo(f"  - {name}")
        if not click.confirm("Do you want to continue with the mapping?"):
            return
    
    user_manager.add_user_mapping(git_name, canonical_name)
    click.echo(f"Mapped '{git_name}' to '{canonical_name}'")

@users.command()
@click.argument('canonical-name')
@click.argument('avatar-path', type=click.Path(exists=True))
def set_avatar(canonical_name: str, avatar_path: str):
    """Set an avatar for a user."""
    user_manager = UserManager()
    try:
        user_manager.set_user_avatar(canonical_name, Path(avatar_path))
        click.echo(f"Avatar set for user '{canonical_name}'")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@users.command()
def list():
    """List all user mappings."""
    mappings = user_manager.get_all_users()
    
    if len(mappings) == 0:
        click.echo("No user mappings found.")
        return
    
    click.echo("User Mappings:")
    for git_name, data in mappings.items():
        canonical_name = data['canonical_name']
        avatar = data.get('avatar', 'Not set')
        click.echo(f"  {git_name} -> {canonical_name}")
        click.echo(f"    Avatar: {avatar}")

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main()