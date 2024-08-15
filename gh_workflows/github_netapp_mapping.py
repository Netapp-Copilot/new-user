
import logging
import csv
import json
import requests
import argparse
import datetime
import os
from gql import Client, gql
from gql.transport.exceptions import TransportQueryError
from gql.transport.aiohttp import AIOHTTPTransport

class NetAppGraphQL(object):
    def __init__(self):
        self.headers = {'Authorization': f'token {os.getenv("GH_AUDIT")}'}
        self.url = 'https://api.github.com/graphql'

    def sanitize_headers(self, headers):
        return {k: v.replace('\n', '').replace('\r', '') for k, v in headers.items()}

    def run_query(self, my_query):
        sanitized_headers = self.sanitize_headers(self.headers)
        transport = AIOHTTPTransport(url=self.url, headers=sanitized_headers)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql(my_query)
        # If we don't have permissions to access collaborators (archived repos). Force gql to give us the data
        try:
            data = client.execute(query)
        except TransportQueryError as error:
            data = error.data
        return data

def get_results(graphql, users):
    next_page = True
    after = None
    while next_page:
        results = graphql.run_query(ent_user_mails(after))
        for each in results['enterprise']["ownerInfo"]["samlIdentityProvider"]["externalIdentities"]['edges']:
            users[each['node']['user']['login']] = each['node']['samlIdentity']['username']
        if results["enterprise"]:
            if results["enterprise"]["ownerInfo"]["samlIdentityProvider"]["externalIdentities"]["pageInfo"]["hasNextPage"]:
                after = results["enterprise"]["ownerInfo"]["samlIdentityProvider"]["externalIdentities"]["pageInfo"]["endCursor"]
            else:
                break
    return users

def ent_user_mails(after=None):
    return """
{
  enterprise(slug: "netapp") {
    ownerInfo {
      samlIdentityProvider {
        externalIdentities(first: 100 after:AFTER) {
          pageInfo {
            hasNextPage
            endCursor
          }
          edges{
            node{
              samlIdentity {
                username
              }
              user {
                login
              }
            }
          }
        }
      }
    }
  }
}
""".replace("AFTER", '"{}"'.format(after) if after else "null")

def write_csv_file(users, savefile='/tmp/user-maping.csv'):
    with open(savefile, mode='w') as data:
        data_writer = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_writer.writerow(['Github username', 'Email Addresss'])
        for user in users:
            data_writer.writerow([str(user), str(users[user])])
    permission = 0o644
    os.chmod(f'/github_logs/emails/user-maping.csv', permission)

def get_nag_users(ng):
    """
    Get the list of a user for an NG
    :param ng: The ng we want the list of users from
    :return: A list of email address of people who are on the NG
    """
    response = requests.get('http://onestop.netapp.com/dir/api/ng/{}'.format(ng),
                            headers={'Accept': 'application/vnd.netapp.dir.api+json'})
    netapp_emails2netapp_usernames = {
        each['email'].lower(): each['user_name'] for each in response.json()['payload']
    }
    json.dump(netapp_emails2netapp_usernames, open("netapp_emails2netapp_usernames.json", "w"))

def main():
    options = global_options().parse_args()
    print("Getting the list of users from github...")
    print(datetime.datetime.now())
    graphql = NetAppGraphQL()
    users = {}
    users = get_results(graphql, users)
    print(datetime.datetime.now())
    print("writing the csv file")
    write_csv_file(users)
    #json.dump(users, open("user_email.json", "w"))

    logging.info(f"Getting the mapping of netap emails to netapp usernames...")
    get_nag_users("ng-github-users")

def global_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='WARNING')
    return parser


if __name__ == "__main__":
    main()