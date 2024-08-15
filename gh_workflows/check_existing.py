import argparse
import requests
import sys

def main():
    options = parse_args()
    results = query_enterprise('consumed-licenses', options.token)
    for each in results:
        print(results)
        for user in each['users']:
            if user['github_com_login'] == options.github:
                print(f"User {options.username} is consuming a license")
                sys.exit(0)
    else:
        print(f"User {options.username} is not consuming a license")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', dest='username', help="GitHub useranme")
    parser.add_argument('--token', dest='token', help="GitHub token")
    return parser.parse_args()


def query_enterprise(api, token, give_params=None, additional_headers=None):
    query_url = f"https://api.github.com/enterprises/netapp/{api}"
    headers = {'Authorization': f'token {token}'}
    if additional_headers:
        headers.update(additional_headers)
    params = {"per_page": "100"}
    response = _make_request(query_url, headers, params)
    data = [response.json()]
    while 'next' in response.links:
        response = _make_request(response.links['next']['url'], headers)
        data.append(response.json())
    return data

def _make_request(url, headers, params=None):
    return requests.get(url, headers=headers, params=params)


if __name__ == "__main__":
    main()