"""GitHub 适配器：清理 Release（可选删 tag）。"""
import requests
from ...core.http import build_headers
from ...core.models import Resource

BASE = "https://api.github.com"
ENV_TOKEN = "GITHUB_TOKEN"


class GitHubAdapter:
    display_name = "GitHub Release"
    token_env = ENV_TOKEN

    def __init__(self, token, delete_tags=False):
        self.token = token
        self.delete_tags = delete_tags
        self.headers = build_headers(token, extra={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def list_groups(self):
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

    def list_resources(self, full_name):
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
            for rel in d:
                out.append(Resource(
                    id=str(rel["id"]),
                    label=f"{rel.get('tag_name')} ({rel.get('name') or ''})",
                    created_at=rel.get("created_at") or "",
                    raw=rel,
                ))
            if len(d) < 100:
                break
            page += 1
        return out

    def delete_resource(self, full_name, res):
        owner, repo = full_name.split("/", 1)
        url = f"{BASE}/repos/{owner}/{repo}/releases/{res.id}"
        try:
            r = requests.delete(url, headers=self.headers)
        except requests.RequestException as e:
            return False, f"请求异常: {e}"
        if r.status_code not in (200, 204):
            return False, f"[{r.status_code}] {r.text[:200]}"

        if self.delete_tags and res.raw.get("tag_name"):
            tag = res.raw["tag_name"]
            tag_url = f"{BASE}/repos/{owner}/{repo}/git/refs/tags/{tag}"
            try:
                r2 = requests.delete(tag_url, headers=self.headers)
                if r2.status_code not in (200, 204, 422):
                    return True, f"release 已删, tag 删除失败 [{r2.status_code}]"
            except requests.RequestException as e:
                return True, f"release 已删, tag 异常: {e}"
        return True, None
