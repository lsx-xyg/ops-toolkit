"""Vercel API 封装。所有 action 共用这里的方法。"""
import requests
from ...core.http import build_headers

BASE = "https://api.vercel.com"


class VercelClient:
    token_env = "VERCEL_TOKEN"

    def __init__(self, token):
        self.token = token
        self.headers = build_headers(token, extra={"Content-Type": "application/json"})

    def list_projects(self):
        projects = []
        url = f"{BASE}/v9/projects"
        params = {"limit": 100}
        while url:
            r = requests.get(url, headers=self.headers, params=params)
            if r.status_code in (401, 403):
                raise Exception(f"Vercel 认证失败 [{r.status_code}]")
            r.raise_for_status()
            d = r.json()
            projects.extend((p["id"], p["name"]) for p in d.get("projects", []))
            nxt = d.get("pagination", {}).get("next")
            if nxt:
                params["until"] = nxt
                params["from"] = None
            else:
                url = None
        return projects

    def list_deployments(self, project_id):
        out = []
        url = f"{BASE}/v7/deployments"
        params = {"limit": 100, "projectId": project_id}
        while url:
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            d = r.json()
            out.extend(d.get("deployments", []))
            nxt = d.get("pagination", {}).get("next")
            if nxt:
                params["until"] = nxt
                params["from"] = None
            else:
                url = None
        return out

    def delete_deployment(self, deployment_id):
        url = f"{BASE}/v13/deployments/{deployment_id}"
        r = requests.delete(url, headers=self.headers)
        return r.status_code == 200, (None if r.status_code == 200 else f"[{r.status_code}] {r.text[:200]}")
