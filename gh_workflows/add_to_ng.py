import requests
import urllib.parse
import json
import os
import argparse

def main():
    options = parse_args()
    # Initial parameters
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    scope = os.getenv("SCOPE")
    oauth_data = get_oauth_token(tenant_id, client_id, client_secret, scope)
    add_user_to_nag(oauth_data, options.username)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', help="Netapp useranme")
    return parser.parse_args()

def get_nag_users(oauth_data):
    headers = {
        'Authorization': f"{oauth_data['token_type']} {oauth_data['access_token']}",
        'Content-Type': "application/json"
    }
    # Make the API request
    function_url = "https://nagapi.netapp.com/api/nag/ng-github-users" + "?impersonateuser=githubna@netapp.com&loadtype=2"
    result_response = requests.get(function_url, headers=headers)
    # Print out the response text before parsing it
    print("API response:")
    print(result_response.text)

    # Parse the JSON response and print the result
    result_data = result_response.json()
    print(result_data)
    print(len(result_data['Roles']))
    with open('ng_github_users.json', 'w') as f:
        f.write(result_response.text)

def add_user_to_nag(oauth_data, username):
    headers = {
        'Authorization': f"{oauth_data['token_type']} {oauth_data['access_token']}",
        'Content-Type': "application/json"
    }
    body = {
        'Roles':[{'Name': username, 'IsMember': 'yes'}]
    }
    function_url_put = "https://nagapi.netapp.com//api/nag/ng-github-users" + "?impersonateuser=githubna@netapp.com"
    result_response = requests.put(function_url_put, headers=headers, data=json.dumps(body))
    # Print out the response text before parsing it
    print("API PUT response:")
    print(result_response.text)

    # Parse the JSON response and print the result
    result_data = result_response.json()
    print(result_data)



def get_oauth_token(tenant_id, client_id, client_secret, scope):
    # Construct the URL and headers for the token request
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Construct the request body for the token request
    auth_body = {
        "grant_type": "client_credentials",
        "scope": urllib.parse.quote(scope),
        "client_id": client_id,
        "client_secret": client_secret
    }

    # Make the request
    oauth_response = requests.post(url, data=auth_body, headers=headers)

    # Parse the JSON response
    oauth_data = oauth_response.json()

    return oauth_data

if __name__ == "__main__":
    main()
