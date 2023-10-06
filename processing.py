import asyncio
import time
from collections import Counter


class Processing:
    def __init__(self, client):
        self._client = client

    def process(self, org_name, need_forks):
        organisation = self.get_organisation(org_name)

        repos = self.get_repos(org_name, organisation, need_forks)

        time.sleep(0.2)
        print('\n Get count commits:')
        count_commits = self.get_count_commits(repos)

        time.sleep(0.2)
        print('\nScanning commits:')
        return self.handle_all_commits_and_count_users(count_commits)

    def get_organisation(self, org_name):
        org_task = self._client.get_organization(org_name)
        return asyncio.run(org_task)

    def get_repos(self, org_name, organisation, forks):
        repos_task = self._client.get_repos(org_name, organisation.public_repos)
        rep = asyncio.run(repos_task)
        return [j for i in rep for j in i if (j.fork == 0 and forks == 0) or forks]

    def get_count_commits(self, repos):
        count_commits_task = self._client.get_count_commits(repos)
        return asyncio.run(count_commits_task)

    def handle_all_commits_and_count_users(self, count_commits):
        users = Counter()
        commits_task = self._client.get_commits(count_commits)
        commits_list = asyncio.run(commits_task)
        for commits in commits_list:
            users += commits
        return users
