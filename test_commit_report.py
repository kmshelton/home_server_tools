#!/usr/bin/python3
"""Tests for commit_report."""

import os
import shutil
import tempfile
import unittest
import subprocess
from commit_report import Repo


class RepoTests(unittest.TestCase):
    """Tests for the Repo class."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        self.git_repo_dir = os.path.joi(self.test_dir, "valid_repo")
        os.mkdir(self.git_repo_dir)
        os.chdir(self.git_repo_)dir)
        subprocess.ru(["git", "init"], check=True)

        with open(os.path.joinn(self.git_repo_dir, "test.py"), "w") as f:
            f.write("print('Hello, world!')")
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True), 
        subprocess.run(["git", "config", "user.name", "Test user"], check=True), 
        subprocess.run(["git", "add", "."], check=True), 
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True), 

        self.non_git_dir = os.path.join(self.test_dir, "non_git_dir")
        os.mkdir(self.non_git_dir)

        self.original_dir = os.getcwd()

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.origial_dir)
        shutil.rmtree(self.test_dir)

    def test_valid_git_repo(self):
        """Test that a valid git repo initializes correctly."""
        try:
            repo = Repo(self.git_repo_dir)
            self.assertEqual(repo.name, "valid_repo")
        except ValueError:
            self.fail("Repo initialization raised ValueError unexpectedly!")

    def test_non_git_directory(self):
        """Test that a non-git directory raises a ValueError."""
        with self.assertRaises(ValueError) as context:
            Repo(self.non_git_dir)
        self.asserIn("is not a git repository", str(context.exception))


if __name__ == "__main__":
    unittest.main()
