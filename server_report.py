#!/usr/bin/python3
"""Tool to generate a report about server state."""

import argparse
import datetime
import logging
import subprocess
import sys
import lib.notify


def get_disk_usage() -> str:
    """Get disk usage iformation.

    Returns:
        Disk usage information as a string
    """
    result = subprocess.run(['df', '-h'],
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout


def get_uptime() -> str:
    """Get system uptime information.

    Returns:
        System uptime as a string
    """
    result = subprocess.run(['uptime'],
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout


def generate_report() -> str:
    """Generate the server state report.

    Returns:
        Report contents as a string
    """
    sections = [("Disk Usage", get_disk_usage()),
                ("System Uptime", get_uptime())]

    report_parts = []
    for title, content in sections:
        report_parts.append(f"=== {title} ===\n{content}\n")

    return "\n".join(report_parts)


def parse_arguments():
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Server state reporter")
    parser.add_argument(
        '--debug',
        action='store_true',
        help='display debugging info and don\'t mail the report')
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

    email_subject = f'Server Report {datetime.datetime.now()}'
    email_body = generate_report()

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
