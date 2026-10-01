"""GitHub API 封装。以后加任何 GitHub 功能都复用这里。"""
import requests
from ...core.http import build_headers

BASE = "https://api.github.com"


class GitHubClient:
    token_env = "GITHUB_TOKEN"

    def __init__(self, token):
        self.token = token
        self.headers = build_headers(token, extra={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def list_repos(self):
        repos = []
        page = 1
        while True:
            r = requests.get(
                f"{BASE}/user/repos", headers=self.headers,
                params={"per_page": 100, "page": page, "sort": "updated"},
            )
            if r.status_code == 401:
                raise Exception("GitHub Token 无效")
            r.raise_for_status()
            d = r.json()
            if not d:
                break
            repos.extend((x["full_name"], x["full_name"]) for x in d)
            if len(d) < 100:
                break
            page += 1
        return repos

    # -------- Release --------
    def list_releases(self, full_name):
        owner, repo = full_name.split("/", 1)
        out = []
        page = 1
        while True:
            r = requests.get(
                f"{BASE}/repos/{owner}/{repo}/releases", headers=self.headers,
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            d = r.json()
            if not d:
                break
            out.extend(d)
            if len(d) < 100:
                break
            page += 1
        return out

    def delete_release(self, full_name, release_id):
        owner, repo = full_name.split("/", 1)
        r = requests.delete(f"{BASE}/repos/{owner}/{repo}/releases/{release_id}",
                            headers=self.headers)
        if r.status_code not in (200, 204):
            return False, f"[{r.status_code}] {r.text[:200]}"
        return True, None

    def delete_tag(self, full_name, tag):
        owner, repo = full_name.split("/", 1)
        r = requests.delete(f"{BASE}/repos/{owner}/{repo}/git/refs/tags/{tag}",
                            headers=self.headers)
        if r.status_code in (200, 204, 422):
            return True, None
        return False, f"[{r.status_code}] {r.text[:200]}"

    # -------- 未来可加：workflow runs / packages / branches / issues --------
    # def list_workflow_runs(self, full_name): ...
    # def delete_workflow_run(self, full_name, run_id): ...
    # def list_packages(self, full_name): ...
