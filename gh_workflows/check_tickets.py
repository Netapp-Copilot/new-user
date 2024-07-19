import requests
import os
import re

info_pattern = re.compile(r'### Netapp Username\s*\n\s*(\S+)')


def main():
    token = os.getenv("ADMIN_GITHUB_TOKEN")
    token = token.strip()

    # GitHub API URL for listing issues of a specific repository
    url = f'https://api.github.com/repos/Netapp-Copilot/new-user/issues'

    # Make a GET request to the GitHub API
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)

    ng_usernames = get_ng_users()

    # Check if the request was successful
    if response.status_code == 200:
        issues = response.json()
        for issue in issues:
            netapp_username = get_netapp_username(issue)
            github_username = issue['user']['login']
            if not netapp_username:
                print(f"Failed to retrieve NetApp Username from issue: [{issue['title']}]({issue['html_url']})")
                continue
            netapp_username = netapp_username.lower()
            if netapp_username in ng_usernames:
                print(f"Adding user {github_username} to Copilot")
                add_user_to_team(github_username, token)
                comment_on_issue(issue['number'], f"User {github_username} has been added to Copilot", token)
                close_issue(issue['number'], token)
    else:
        print(f"Failed to retrieve issues. Status code: {response.status_code}")

def get_netapp_username(issue):
        # Extract NetApp username from the issue body
    match = info_pattern.search(issue['body'])
    print(issue['body'])
    if match:
        netapp_username = match.group(1)
        print(netapp_username + " found")
        return netapp_username
    else:
        print(f"Issue: {issue['title']} - NetApp Username not found")
        return False
    
def add_user_to_team(username, token):
    """Add a user to the team."""
    print(f"Adding user {username} to Copilot")
    headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',}
    url = f'https://api.github.com/orgs/Netapp-Copilot/teams/active-users/memberships/{username}'
    response = requests.put(url, headers=headers)
    print(response)
    return response.status_code == 200

def comment_on_issue(issue_number, comment, token):
    """Post a comment on an issue."""
    print(f"Commenting on issue {issue_number}")
    headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',}
    url = f'https://api.github.com/repos/Netapp-Copilot/active-users/issues/{issue_number}/comments'
    data = {'body': comment}
    response = requests.post(url, json=data, headers=headers)
    print(response)
    print(response.json())
    return response.status_code == 201

def close_issue(issue_number, token):
    """Close an issue."""
    print(f"Closing issue {issue_number}")
    headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',}
    url = f'https://api.github.com/repos/Netapp-Copilot/active-users/issues/{issue_number}'
    data = {'state': 'closed'}
    response = requests.patch(url, json=data, headers=headers)
    print(response)
    print(response.json())
    return response.status_code == 200

def get_ng_users():
    response = requests.get('http://onestop.netapp.com/dir/api/ng/ng-github-users',
                            headers={'Accept': 'application/vnd.netapp.dir.api+json'})
    usernames = {
        each['user_name'].lower(): each['email'] for each in response.json()['payload']
    }
    return usernames


if __name__ == "__main__":
    main()