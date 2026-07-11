#!/usr/bin/env python3
"""
today.py — refreshes the live numbers on dark_mode.svg / light_mode.svg.

Runs inside GitHub Actions (see .github/workflows/main.yml). Needs a
repository secret ACCESS_TOKEN containing a Personal Access Token with
`repo` + `read:user` scopes (classic) or "Contents: read" + "Metadata: read"
(fine-grained) so it can read private repos and user contribution data too.

What it fills in, by SVG element id:
    repo_data      total public+private repos you own
    contrib_data   total repos you've contributed to (owned + collaborator)
    star_data      total stargazers across your owned repos
    commit_data    total commits you've authored, all-time
    follower_data  follower count
    loc_data       net lines of code currently in your owned repos (HEAD)
    loc_add        total lines added, all-time, across owned repos
    loc_del        total lines deleted, all-time, across owned repos
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import requests

USER_NAME = os.environ.get("USER_NAME", "anand-esc")
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
HEADERS = {"Authorization": f"bearer {ACCESS_TOKEN}"}
API = "https://api.github.com/graphql"

SVG_FILES = ["dark_mode.svg", "light_mode.svg"]


def gql(query, variables=None):
    r = requests.post(API, json={"query": query, "variables": variables or {}}, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def account_created_year():
    q = """
    query($login: String!) { user(login: $login) { createdAt } }
    """
    d = gql(q, {"login": USER_NAME})
    return int(d["user"]["createdAt"][:4])


def total_commits():
    """Sum totalCommitContributions year-by-year since account creation."""
    start_year = account_created_year()
    this_year = datetime.now(timezone.utc).year
    total = 0
    q = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    for year in range(start_year, this_year + 1):
        frm = f"{year}-01-01T00:00:00Z"
        to = f"{year}-12-31T23:59:59Z"
        d = gql(q, {"login": USER_NAME, "from": frm, "to": to})
        cc = d["user"]["contributionsCollection"]
        total += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    return total


def repo_stats():
    """Owned repos: count + total stargazers. Also count of repos contributed to."""
    q = """
    query($login: String!, $after: String) {
      user(login: $login) {
        repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes { name stargazerCount defaultBranchRef { name } }
        }
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT]) {
          totalCount
        }
      }
    }
    """
    repos, stars, after, contrib = [], 0, None, 0
    while True:
        d = gql(q, {"login": USER_NAME, "after": after})
        u = d["user"]
        contrib = u["repositoriesContributedTo"]["totalCount"]
        page = u["repositories"]
        for n in page["nodes"]:
            repos.append(n["name"])
            stars += n["stargazerCount"]
        if page["pageInfo"]["hasNextPage"]:
            after = page["pageInfo"]["endCursor"]
        else:
            break
    return repos, stars, contrib


def followers():
    q = "query($login: String!) { user(login: $login) { followers { totalCount } } }"
    d = gql(q, {"login": USER_NAME})
    return d["user"]["followers"]["totalCount"]


def clone_and_count(repo):
    """Shallow-free clone + `git log --numstat` summed for commits by this user."""
    url = f"https://x-access-token:{ACCESS_TOKEN}@github.com/{USER_NAME}/{repo}.git"
    path = f"/tmp/{repo}"
    try:
        subprocess.run(["git", "clone", "--quiet", "--single-branch", url, path],
                        check=True, timeout=180)
    except Exception as e:
        print(f"  skip {repo}: clone failed ({e})", file=sys.stderr)
        return 0, 0, 0

    fmt = subprocess.run(
        ["git", "-C", path, "log", "--pretty=tformat:", "--numstat",
         f"--author={USER_NAME}"],
        capture_output=True, text=True,
    ).stdout

    add = de = 0
    for line in fmt.splitlines():
        m = re.match(r"^(\d+)\s+(\d+)\s+", line)
        if m:
            add += int(m.group(1))
            de += int(m.group(2))

    net = subprocess.run(
        ["git", "-C", path, "log", "-1", "--pretty=tformat:", "--shortstat"],
        capture_output=True, text=True,
    )
    subprocess.run(["rm", "-rf", path])
    return add, de, add - de


def loc_totals(repos):
    total_add = total_del = 0
    for repo in repos:
        a, d, _ = clone_and_count(repo)
        total_add += a
        total_del += d
        print(f"  {repo}: +{a} -{d}")
    return total_add, total_del


def svg_set(path, updates):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    for elem_id, value in updates.items():
        content = re.sub(
            rf'(id="{re.escape(elem_id)}"[^>]*>)[^<]*(</tspan>)',
            rf'\g<1>{value}\g<2>',
            content,
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print("Fetching repo + star data...")
    repos, stars, contrib = repo_stats()
    print("Fetching commit history...")
    commits = total_commits()
    print("Fetching followers...")
    fol = followers()
    print(f"Computing lines of code across {len(repos)} repos (this can take a while)...")
    add, delete = loc_totals(repos)
    net_loc = add - delete

    updates = {
        "repo_data": f"{len(repos):,}",
        "contrib_data": f"{contrib:,}",
        "star_data": f"{stars:,}",
        "commit_data": f"{commits:,}",
        "follower_data": f"{fol:,}",
        "loc_data": f"{net_loc:,}",
        "loc_add": f"++{add:,}",
        "loc_del": f"--{delete:,}",
    }

    for svg in SVG_FILES:
        if os.path.exists(svg):
            svg_set(svg, updates)
            print(f"Updated {svg}")

    print("Done:", updates)


if __name__ == "__main__":
    main()
