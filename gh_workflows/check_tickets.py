import requests
import os
import re
from datetime import datetime, timedelta, timezone

info_pattern = re.compile(r'### Netapp SSO Username.*?\n\s*(\S+)', re.DOTALL)
owners = ['suhasbshekar', 'carchi8py', 'wenjun666', 'chuyich']


def main():
    token = os.getenv("ADMIN_GITHUB_TOKEN")
    token = token.strip()

    # GitHub API URL for listing issues of a specific repository
    url = f'https://api.github.com/repos/Netapp-Copilot/new-user/issues'

    # Make a GET request to the GitHub API
    headers = {'Authorization': f'token {token}'}
    response = requests.get(url, headers=headers)
    print(response)

    ng_usernames = get_ng_users()

    # Check if the request was successful
    if response.status_code == 200:
        issues = response.json()
        for issue in issues:
            try:
                netapp_username = get_netapp_username(issue)
            except:
                print(f"Failed to retrieve NetApp Username from issue: [{issue['title']}]({issue['html_url']})")
                continue
            github_username = issue['user']['login']
            print(github_username)
            if not netapp_username:
                print(f"Failed to retrieve NetApp Username from issue: [{issue['title']}]({issue['html_url']})")
                continue
            netapp_username = netapp_username.lower()
            if netapp_username in ng_usernames:
                print(f"NetApp username {netapp_username} found in NG directory")
                created_at_str = issue['created_at']  # The creation time in ISO 8601 format
                created_at = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%SZ')  # Parse the creation time
                created_at = created_at.replace(tzinfo=timezone.utc)  # Make it timezone-aware, adjust accordingly
                now = datetime.now(timezone.utc)  # Current time in UTC, adjust if using a different timezone
                time_diff = now - created_at
                # If the ticket is older than an hour check to see if they are on the NG
                if time_diff >= timedelta(minutes=60):
                    print(f"Adding user {github_username} to Copilot")
                    id = get_user_id(github_username, token)
                    invite_user_to_org_and_add_to_team(id, token)
                    comment_on_issue(issue['number'], 
                                    "User " + github_username + " has been added to Copilot.\n"
                                    "For SecLab/BigTop users there are special steps on the confluence page that need to be followed to complete the setup https://confluence.ngage.netapp.com/display/NGAGE/Copilot\n"
                                    "For OpenLab users please follow the standard steps here https://docs.github.com/en/copilot/using-github-copilot/getting-code-suggestions-in-your-ide-with-github-copilot", 
                                    token)
                    close_issue(issue['number'], token)
                # If the ticket is older than 24 hours asign admins to ticket
                elif time_diff >= timedelta(hours=24):
                    print(f"Assigning admins to issue {issue['number']}")
                    comment_on_issue(issue['number'], 
                                    github_username + " we have not seen + " + netapp_username + " in the NG directory yet, the admins will reach out to you shortly.",token)
                    assign_users_to_issue(issue['number'], owners, token)
                    
            else:
                print(f"NetApp username {netapp_username} not found in NG directory")
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

def invite_user_to_org_and_add_to_team(user_id, token):
    """Invite a user to the GitHub organization and add them to the active-users team."""
    print(f"Inviting user {user_id} to the GitHub organization and adding to active-users team")

    # Invite user to the organization
    invite_url = f'https://api.github.com/orgs/Netapp-Copilot/invitations'
    invite_headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    invite_data = {
        'invitee_id': user_id,
        'role': 'direct_member',
        'team_ids': [8276605]
    }
    invite_response = requests.post(invite_url, headers=invite_headers, json=invite_data)
    print(invite_data)
    print(invite_response)
    print(invite_response.json())

def get_user_id(username, token):
    """Get the GitHub user ID for a given username."""
    url = f'https://api.github.com/users/{username}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        return user_data['id']
    else:
        print(f"Failed to retrieve user ID. Status code: {response.status_code}")
        print(response.json())
        return None

def comment_on_issue(issue_number, comment, token):
    """Post a comment on an issue."""
    print(f"Commenting on issue {issue_number}")
    headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',}
    url = f'https://api.github.com/repos/Netapp-Copilot/new-user/issues/{issue_number}/comments'
    data = {'body': comment}
    response = requests.post(url, json=data, headers=headers)
    print(response)
    print(response.json())
    return response.status_code == 201

def close_issue(issue_number, token):
    """Close an issue."""
    print(f"Closing issue {issue_number}, if you have any issues please reach out to ng-github-admins@netapp.com")
    headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',}
    url = f'https://api.github.com/repos/Netapp-Copilot/new-user/issues/{issue_number}'
    data = {'state': 'closed'}
    response = requests.patch(url, json=data, headers=headers)
    print(response)
    print(response.json())
    return response.status_code == 200

def assign_users_to_issue(issue_number, assignees, token):
    """
    Assigns users to a GitHub issue.

    Parameters:
    - issue_number: The number of the issue to assign users to.
    - assignees: A list of GitHub usernames to assign to the issue.
    - token: GitHub API token for authentication.
    """
    url = f"https://api.github.com/repos/Netapp-Copilot/new-user/issues/{issue_number}/assignees"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"assignees": assignees}
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        print(f"Successfully assigned {', '.join(assignees)} to issue #{issue_number}")
    else:
        print(f"Failed to assign users to issue #{issue_number}. Status code: {response.status_code}")

def get_ng_users():
    response = requests.get('http://onestop.netapp.com/dir/api/ng/ng-github-users',
                            headers={'Accept': 'application/vnd.netapp.dir.api+json'})
    usernames = {
        each['user_name'].lower(): each['email'] for each in response.json()['payload']
    }
    return usernames


if __name__ == "__main__":
    main()
