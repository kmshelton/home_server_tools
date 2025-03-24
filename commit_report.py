#!/usr/bin/python3
"""Tool to generate a report about git repos in a given directory."""

import argparse
import datetime
import logging
import os
import re
import subprocess
import sys
from typing import Dict, List, Set
from dataclasses import dataclass
import lib.notify


@dataclass
class Repo:
    """A class representing a collection of git repos."""
    name: str
    commits_from_last_day: str
    commits_from_last_week: str
    commits: str
    commit_count_from_last_day: int
    commit_count_from_last_week: int
    line_counts: Dict[str, int]

    SUPPORTED_LANGUAGES = {
        'Python': ['.py'],
        'Golang': ['.go'],
        'Bash': ['.sh'],
        'C': ['.c'],
        'Rust': ['.rs'],
        'C++': ['.cc'],
        'Assembly': ['.s', '.asm']
    }

    @classmethod
    def from_directory(cls, repo_dir: str) -> 'Repo':
        """Create a Repo instance from a directory path.

        Args:
            A new Repo instance

        Raises:
            ValueError: If the directory is not a git repository
        """
        abs_repo_dir = os.path.abspath(repo_dir)

        if not _is_git_repo(abs_repo_dir):
            raise ValueError(f"Directory '{repo_dir}' is not a git repository")

        os.chdir(abs_repo_dir)
        name = os.path.basename(abs_repo_dir)

        commits_from_last_day = _run_git_command(
            'git log --oneline --since="1 day ago"')
        commits_from_last_week = _run_git_command(
            'git log --oneline --since="7 days ago"')
        commits = _run_git_command('git log --date=short')

        commit_count_from_last_day = commits_from_last_day.count('\n')
        commit_count_from_last_week = commits_from_last_week.count('\n')

        line_counts = {}
        for lang, extensions in cls.SUPPORTED_LANGUAGES.items():
            line_counts[lang] = sum(
                _count_lines_by_extension(ext) for ext in extensions)

        return cls(name=name,
                   commits_from_last_day=commits_from_last_day,
                   commits_from_last_week=commits_from_last_week,
                   commits=commits,
                   commit_count_from_last_day=commit_count_from_last_day,
                   commit_count_from_last_week=commit_count_from_last_week,
                   line_counts=line_counts)

    def __str__(self) -> str:
        """String representation of the repository."""
        return (
            f"Repo(name: {self.name}\n"
            f"commits from last day: {self.commits_from_last_day}\n"
            f"commits from last week: {self.commits_from_last_week}\n"
            f"commit count from last day: {self.commit_count_from_last_day}\n"
            f"commit count from last week: {self.commit_count_from_last_week}\n"
            f"line_counts: {self.line_counts})")


def _is_git_repo(directory: str) -> bool:
    """Check if a directory is a git repository.

    Args:
        directory: Path to check

    Returns:
        True if the directory is a git repository, False otherwise
    """
    current_dir = os.getcwd()
    try:
        os.chdir(directory)
        subprocess.check_output('git rev-parse --is-inside-work-tree',
                                shell=True,
                                text=True)
        result = True
    except subprocess.CalledProcessError:
        result = False
    finally:
        os.chdir(current_dir)
    return result


def _run_git_command(command: str) -> str:
    """Run a git command and return its output.

    Args:
        command: Git command to run

    Returns:
        Command output as a string
    """
    return str(subprocess.check_output(command, shell=True, text=True))


def _count_lines_by_extension(file_extension: str) -> int:
    """Count lines of code for files with a specific extension.

    Args:
        file_extension: File extension to count

    Returns:
        Number of lines
    """
    try:
        return int(
            subprocess.check_output(
                # The \\ becomes a single \ in the actual shell command.
                f'git ls-files | grep \'\\{file_extension}$\' | xargs cat | wc -l',
                shell=True,
                text=True))
    except subprocess.CalledProcessError:
        return 0


def get_repositories(repos_dir: str) -> List[Repo]:
    """Get all git repositories in a directory.

    Args:
        repos_dir: Directory containing git repositories

        Returns:
            List of Repo instances
    """
    repos = []
    original_dir = os.getcwd()

    try:
        dir_iterator = os.scandir(repos_dir)
        for directory in dir_iterator:
            if directory.is_dir():
                repo_path = os.path.join(repos_dir, directory.name)
                logging.debug('Checkig directory %s', repo_path)
                try:
                    repos.append(Repo.from_directory(repo_path))
                except ValueError as e:
                    logging.warning(str(e))
    finally:
        os.chdir(original_dir)

    return repos


def calculate_streak(repos: List[Repo]) -> int:
    """Calculate consecutive days with a commit startig with the previous day.

    Args:
        repos: A list of Repo instances

    Returns:
        Number of consecutive days with a commit
    """
    dates_with_a_commit: Set[datetime.date] = set()

    for repo in repos:
        for line in repo.commits.splitlines():
            # Example date from git log --date=short:
            # Date:   2019-10-27
            match = re.search(r'^Date:\s.*(\d{4})-(\d+)-(\d+)', line)
            if match:
                dates_with_a_commit.add(
                    datetime.date(
                        # year
                        int(match.group(1)),
                        # month
                        int(match.group(2)),
                        # day
                        int(match.group(3))))

    date_to_check = datetime.date.today() - datetime.timedelta(1)
    count = 0

    while date_to_check in dates_with_a_commit:
        count += 1
        date_to_check = date_to_check - datetime.timedelta(1)

    return count


def generate_report(repos: List[Repo]) -> str:
    """Generate the commit report.

    Args:
        repos: List of repositories to report on

    Returns:
        Report content as a string
    """
    if not repos:
        return "No git repositores found."

    total_commits_from_last_day = sum(repo.commit_count_from_last_day
                                      for repo in repos)
    total_commits_from_last_week = sum(repo.commit_count_from_last_week
                                       for repo in repos)

    report = [
        f"Commits in the last 24 hours (across all repos): {total_commits_from_last_day}",
        f"Commits in the last week (across all repos): {total_commits_from_last_week}",
        f"Consecutive previous days with a commit: {calculate_streak(repos)}",
        ""
    ]

    for repo in repos:
        report.append(f"Activity from the last week in the {repo.name} repo:")
        if repo.commits_from_last_week:
            report.append(repo.commits_from_last_week)
        else:
            report.append("No activity")
        report.append("")

    if repos:
        cumulative_line_counts = {
            lang: 0
            for lang in repos[0].SUPPORTED_LANGUAGES
        }
        for repo in repos:
            for language, count in repo.line_counts.items():
                cumulative_line_counts[language] += count

        report.append("Total current lines (across all repos) of...")
        for language, count in cumulative_line_counts.items():
            report.append(f"{language}: {count}")

    return "\n".join(report)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Git repository commit reporter")
    parser.add_argument(
        '--debug',
        action='store_true',
        help='display debugging info and don\'t mail the report')
    parser.add_argument(
        '--repos_dir',
        type=str,
        required=True,
        help='directory that contains the repos that you want to report on')
    parser.add_argument('--gmail_username',
                        type=str,
                        help='your gmail username')
    parser.add_argument(
        '--app_password',
        type=str,
        help='password to authorize commit_report to send mail as you')

    return parser.parse_args()


def main():
    """Build and send the report."""
    args = parse_arguments()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        repos = get_repositories(args.repos_dir)
    except FileNotFoundError:
        logging.error("Repository directory not found: %s", args.repos_dir)
        return 1

    for repo in repos:
        logging.debug(str(repo))

    email_body = generate_report(repos)

    email_subject = f'Commit Report {datetime.datetime.now()}'

    if not args.debug:
        if not args.gmail_username or not args.app_password:
            logging.error(
                "Gmail username and app password required to send the report email."
            )
            return 1
        lib.notify.mail(args.gmail_username, args.app_password, email_subject,
                        email_body)
    else:
        print(email_body)

    return 0


if __name__ == "__main__":
    sys.exit(main())
