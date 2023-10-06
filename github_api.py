import json
import re
from collections import Counter
from http import HTTPStatus
from math import ceil

import aiohttp
from aiohttp import ClientTimeout
from tqdm.asyncio import tqdm

from models import ErrorObj, RateLimit, Organization, LimitTypes, Repo

regex_for_search_count_commits = re.compile('(?<=&page=)\d+')


class GitHubApi:
    def __init__(self, token: str):
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self._base_url = "https://api.github.com"
        self._timeout = 100

    async def get_rate_left(self) -> RateLimit | ErrorObj:
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=self._timeout)) as session:
            async with session.get(self._base_url + '/rate_limit', headers=self._headers) as response:
                status, text = response.status, await response.text()
                if status == HTTPStatus.OK:
                    body = json.loads(text)
                    return RateLimit(limit_type=LimitTypes.core,
                                     **body['resources']['core'])
                else:
                    return ErrorObj(text, status)

    async def get_organization(self, org: str) -> Organization | ErrorObj:
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=self._timeout)) as session:
            async with session.get(self._base_url + f'/orgs/{org}', headers=self._headers) as response:
                status, text = response.status, await response.text()
                if status == HTTPStatus.OK:
                    body = json.loads(text)
                    return Organization(**body)
                else:
                    return ErrorObj(text, status)

    async def _get_repos(self, org_name, page):
        repos = []
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=self._timeout)) as session:
            async with session.get(self._base_url + f'/orgs/{org_name}/repos', headers=self._headers,
                                   params={'per_page': 100, 'page': page, 'type': 'public'}) as response:
                status, text = response.status, await response.text()
                if status == HTTPStatus.OK:
                    body = json.loads(text)
                    for repo in body:
                        repos.append(Repo(**repo))
        return repos

    async def get_repos(self, org_name: str, count: int):
        tasks = []
        for page in range(0, ceil(count / 100)):
            tasks.append(self._get_repos(org_name, page))

        return await tqdm.gather(*tasks)

    async def _get_commits(self, page, commits_url) -> Counter:
        users = Counter()
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=self._timeout)) as session:
            async with session.get(self._base_url + commits_url.split(self._base_url)[1].split('{')[0],
                                   headers=self._headers,
                                   params={'per_page': 100, 'page': page}) as response:

                status, text = response.status, await response.text()
                if status == HTTPStatus.OK:
                    body = json.loads(text)
                    for commit in body:
                        commit_message = commit['commit']['message']
                        if 'merge pull request' in commit_message.lower():
                            continue
                        author = commit['commit']['author']
                        users[author['email']] += 1
        return users

    async def get_commits(self, repos):
        tasks = []
        for repo, count in repos:
            for page in range(0, ceil(count / 100)):
                tasks.append(self._get_commits(page, repo.commits_url))
        return await tqdm.gather(*tasks)

    async def _get_count_commits(self, repo, commits_url):
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=self._timeout)) as session:
            async with session.get(self._base_url + commits_url.split(self._base_url)[1].split('{')[0],
                                   headers=self._headers,
                                   params={'per_page': 1}) as response:
                if response.status == HTTPStatus.OK:
                    count = int(re.findall(regex_for_search_count_commits, response.headers['Link'])[-1])
                    return repo, count

    async def get_count_commits(self, repos):
        tasks = []
        for repo in repos:
            tasks.append(self._get_count_commits(repo, repo.commits_url))
        return await tqdm.gather(*tasks)
