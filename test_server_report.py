#!/usr/bin/python3
"""Tests for server_report.py"""

import unittest
from unittest.mock import patch
import server_report


class TestServerReport(unittest.TestCase):
    """Test cases for server_report.py"""

    @patch('server_report.get_disk_usage')
    @patch('server_report.get_uptime')
    def test_generate_report(self, mock_get_uptime, mock_get_disk_usage):
        """Test that generate_report produces correctly formatted output"""
        mock_get_disk_usage.return_value = (
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   20G   80G  20% /")
        mock_get_uptime.return_value = (
            " 22:30:01 up 7 days, 4:03,  2 users,  load average: 0.08, 0.03, 0.01"
        )

        report = server_report.generate_report()

        expected_report = (
            "=== Disk Usage ===\n"
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   20G   80G  20% /\n"
            "\n"
            "=== System Uptime ===\n"
            " 22:30:01 up 7 days, 4:03,  2 users,  load average: 0.08, 0.03, 0.01\n"
        )

        self.assertEqual(report, expected_report)


if __name__ == "__main__":
    unittest.main()
