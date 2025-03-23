#!/usr/bin/python3
"""Tool to generate a report about git repos in a given directory."""

import argparse
import datetime
import logging
import os
import re
import subprocess
import lib.notify


# pylint: disable=R0903
class Repo:
    """A class representing a collection of git repos."""
    SUPPORTED_LANGUAGES = {
        'Python': ['.py'],
        'Golang': ['.go'],
        'Bash': ['.sh'],
        'C': ['.c'],
        'Rust': ['.rs'],
        'C++': ['.cc'],
        'Assembly': ['.s', '.asm']
    }

    def __init__(self, repo_dir):
        os.chdir(repo_dir)
        try:
            subprocess.check_output('git rev-parse --is-inside-work-tree',
                                    shell=True,
                                    universal_newlines=True)
        except subprocess.CalledProcessError:
            raise ValueError(f"Directory '{repo_dir}' is not a git repository")
        self.name = os.path.basename(repo_dir)
        self.commits_from_last_day = str(
            subprocess.check_output('git log --oneline --since=\'1 day ago\'',
                                    shell=True,
                                    universal_newlines=True))
        self.commits_from_last_week = str(
            subprocess.check_output('git log --oneline --since=\'7 days ago\'',
                                    shell=True,
                                    universal_newlines=True))
        self.commits = str(
            subprocess.check_output('git log --date=short',
                                    shell=True,
                                    universal_newlines=True))
        self.commit_count_from_last_day = self.commits_from_last_day.count(
            '\n')
        self.commit_count_from_last_week = self.commits_from_last_week.count(
            '\n')
        self.line_counts = {}
        for lang, extensions in self.SUPPORTED_LANGUAGES.items():
            self.line_counts[lang] = sum(
                self._line_counter(ext) for ext in extensions)

    def __str__(self):
        return ('Repo(name: ' + self.name + '\ncommits from last day: ' +
                self.commits_from_last_day + '\ncommits from last week: ' +
                self.commits_from_last_week +
                '\ncommit count from last day: ' +
                str(self.commit_count_from_last_day) +
                '\ncommit count from last week: ' +
                str(self.commit_count_from_last_week) + '\nline_counts: ' +
                str(self.line_counts) + ')')

    def _line_counter(self, file_extension):
        return int(
            subprocess.check_output('git ls-files | grep \\' + file_extension +
                                    '$ | xargs cat | wc -l',
                                    shell=True,
                                    universal_newlines=True))


def streak_checker(repos):
    """Calculate consecutive days with a commit starting with the previous day.
 
     Args:
        repos: A list of Repo instances

     Returns:
        count (int): number of consecutive days with a commit.
    """
    dates_with_a_commit = []
    for repo in repos:
        for line in repo.commits.splitlines():
            # Example date from git log --date=short:
            # Date:   2019-10-27
            match = re.search(r'^Date:\s.*(\d{4})-(\d.*)-(\d.*)', line)
            if match:
                dates_with_a_commit.append(
                    datetime.date(int(match.group(1)), int(match.group(2)),
                                  int(match.group(3))))
    date_to_check = datetime.date.today() - datetime.timedelta(1)
    count = 0
    while date_to_check in dates_with_a_commit:
        count += 1
        date_to_check = date_to_check - datetime.timedelta(1)
    return count


def main():
    """Build and send the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug',
        action=store_true,
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
    args = parser.parse_args()
    if args.debug is True:
        logging.basicConfig(level=logging.DEBUG)
    repos = []
    dir_iterator = os.scandir(args.repos_dir)
    for directory in dir_iterator:
        if directory.is_dir():
            logging.debug('Initializing a Repo object for the %s directory',
                          str(directory))
            try:
                repos.append(Repo(os.path.join(args.repos_dir, directory)))
            except ValueError as e:
                loggig.warning(str(e))
                continue

    for repo in repos:
        logging.debug(str(repo))

    total_commits_from_last_day = 0
    total_commits_from_last_week = 0
    for repo in repos:
        total_commits_from_last_day += repo.commit_count_from_last_day
        total_commits_from_last_week += repo.commit_count_from_last_week

    email_body = ('Commits in the 24 hours (across all repos): ' +
                  str(total_commits_from_last_day) +
                  '\nCommits in the last week (across all repos): ' +
                  str(total_commits_from_last_week) +
                  '\nConsecutive previous days with a commit: ' +
                  str(streak_checker(repos)) + '\n')

    for repo in repos:
        email_body += ''.join([
            '\nActivity from the last week in the ', repo.name, ' repo:\n',
            (repo.commits_from_last_week
             if repo.commits_from_last_week else 'No activity\n')
        ])

    cumulative_line_counts = dict.fromkeys(repos[0].line_counts.keys(), 0)
    for repo in repos:
        for language in cumulative_line_counts:
            cumulative_line_counts[language] += repo.line_counts[language]

    email_body += '\nTotal current, lines (across all repos) of...'
    for language, count in cumulative_line_counts.items():
        email_body += ''.join(['\n', language, ': ', str(count)])

    logging.debug('The email body is now constructed: %s\n', email_body)

    email_subject = ''.join(['Commit Report ', str(datetime.datetime.now())])

    if not args.debug:
        if not args.gmail_username or not args.app_password:
            logging.error("Gmail username and app password required to send the report email.")
            return 1
        lib.notify.mail(args.gmail_username, args.app_password, email_subject,
                        email_body)


if __name__ == "__main__":
    main()
