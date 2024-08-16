import requests
import os
import re
from datetime import datetime, timedelta, timezone
import argparse
info_pattern = re.compile(r'### Netapp Username\s*\n\s*(\S+)')



def main():
    options = parse_args()
    token = os.getenv("ADMIN_AUDIT")
    print(token)
    token = token.strip()

    issue_number = options.issue_number

    issue = get_issue_body(token, issue_number)
    netapp_username = get_netapp_username(issue)
    print(netapp_username)


def get_netapp_username(issue):
        # Extract NetApp username from the issue body
    match = info_pattern.search(issue['body'])
    if match:
        netapp_username = match.group(1)
        return netapp_username
    else:
        return False
    
def get_issue_body(token, issue_number):
    # GitHub API URL for the specific issue
    url = f'https://api.github.com/repos/Netapp-Copilot/new-user/issues/{issue_number}'

    # Make a GET request to the GitHub API
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        issue_data = response.json()
        return issue_data
    else:
        return f'Error: Unable to fetch issue. Status code: {response.status_code}'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--issue_number', dest='issue_number', help="GitHub useranme")
    return parser.parse_args()


if __name__ == "__main__":
    main()