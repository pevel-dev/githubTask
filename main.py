import asyncio
from collections import Counter
from os import environ

import dotenv
import matplotlib.pyplot as plt

from github_api import GitHubApi
from processing import Processing

bools = {"yes": True, "no": False, '': True}


async def get_rate_cycle(client: GitHubApi):
    return await client.get_rate_left()


def out_result_in_file(results):
    with open(f'result_{len(results)}.csv', 'w+') as file:
        file.write('email;count_commits\n')
        for key, item in results:
            file.write(f'{key};{item}\n')


def out_plt(results, org_name):
    emails = list(map(lambda res: res[0], results))
    counts = list(map(lambda res: res[1], results))
    plt.figure(figsize=(12, 6))
    plt.barh(emails, counts)

    plt.gca().invert_yaxis()

    plt.title(f'Top 10 коммитеров репозитория {org_name} ')
    plt.xlabel('Количество')

    plt.savefig('top10graphic.png', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    dotenv.load_dotenv('.env')
    token = environ.get("GITHUB_API_TOKEN")
    client = GitHubApi(token)

    print(asyncio.run(get_rate_cycle(client)))
    conti = input("Continue? Press enter or enter any symbols for exit: ")
    if len(conti) > 0:
        quit(0)
    org_name = input("Input organisation name: ")
    forks = input("Should forks be taken when calculating? (Yes/No, default=yes): ")
    forks = bools[forks.lower()]

    users = Processing(client).process(org_name, forks)

    if len(users) < 1:
        print("No commits")
    else:
        users = sorted(users.items(), key=lambda x: x[1], reverse=True)
        print(f"Write all users top in result_{len(users)}.csv")
        out_result_in_file(users)
        if len(users) > 100:
            print("Write top 100 users in result_100.csv")
            out_result_in_file(users[:100])
        out_plt(users[:10], org_name)
