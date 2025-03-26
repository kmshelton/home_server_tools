# Home Server Tools

Like most nerds, I run a home server for things like personal git repos, a
database of all my books, and a gitea instance. My current hardware is a
Chromebox flashed with SeaBIOS to enable Ubuntu.

This collection of utilities runs on my home server.  The utilities:
* generate a report of stats about the repos
* generate a report of telemetry from the server itself
* send out email with the reports

Future work includes:
* automatic backup of repos to Google Drive
* diff a webpage

## Email Configuration

Using the email functionality requires
[an app password](https://support.google.com/mail/answer/185833?hl=en).

## Configuring Periodic Execution

The venerable [cron](https://manpages.debian.org/unstable/cron/cron.8.en.html)
is the best way to set up periodic execution of these utilities. My crontab
looks something like this:

```
# Edit this file to introduce tasks to be run by cron.
# 
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
# 
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').
# 
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
# 
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
# 
# For example, you can run a backup of all your user accounts
# at 5 a.m every week with:
# 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
# 
# For more information see the manual pages of crontab(5) and cron(8)
# 
# m h  dom mon dow   command

0 7 * * * python3 /home/foo/commit_mail/commit_mail.py --repos_dir='/home/foo/repos' --app_password='bar' --gmail_username='foo'
```

## Pre-commit Hook

Here is the pre-commit hook that I configure locally for this repo:

```
#!/bin/bash

echo "Running codespell..."
codespell --skip="*.git,*.pyc,__pycache__" --quiet-level=2
spell_exit_code=$?

if [ $spell_exit_code -ne 0 ]; then
  echo "Spell check failed. Please fix the typos before committing."
  exit 1
fi

STAGED_PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
if [ -n "$STAGED_PYTHON_FILES" ]; then
  echo "Checking Python formatting with yapf3..."
  yapf3 --diff $STAGED_PYTHON_FILES
  format_exit_code=$?
  if [ $format_exit_code -ne 0 ]; then
    echo "Formatting check failed."
    echo "Run 'yapf3 -i <file>' to fix formatting issues, then stage and try committing again."
    exit 1
  fi

  echo "Running pylint..."
  pylint --output-format=text $STAGED_PYTHON_FILES
  lint_exit_code=$?
  # pylint returns a bitmask exit code, we're looking for 0 (no errors)
  if [ $lint_exit_code -ne 0 ]; then
    echo "Linting failed. Please address the issues, then stage and try committing again."
    exit 1
  fi
else
  echo "No Python files to format or lint. Skipping."
fi

echo "Running unit tests..."
python3 -m unittest discover -p "test_*.py"
test_exit_code=$?

if [ $test_exit_code -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi

echo "Tests passed. Proceeding with commit."
exit 0
```
