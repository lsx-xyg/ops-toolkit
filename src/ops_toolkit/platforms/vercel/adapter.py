"""Vercel 适配器：清理部署。"""
import requests
from ...core.http import build_headers
from ...core.models import Resource

BASE = "https://api.vercel.com"
ENV_TOKEN = "VERCEL_TOKEN"


class VercelAdapter:
    display_name = "Vercel 部署"
    token_env = ENV_TOKEN

    def __init__(self, token):
        self.token = token
        self.headers = build_headers(token, extra={"Content-Type": "application/json"})

    def list_groups(self):
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

    def list_resources(self, project_id):
        out = []
        url = f"{BASE}/v7/deployments"
        params = {"limit": 100, "projectId": project_id}
        while url:
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            d = r.json()
            for dep in d.get("deployments", []):
                out.append(Resource(
                    id=dep["uid"],
                    label=dep.get("url") or dep["uid"],
                    created_at=int(dep.get("created") or 0) / 1000,
                    raw=dep,
                ))
            nxt = d.get("pagination", {}).get("next")
            if nxt:
                params["until"] = nxt
                params["from"] = None
            else:
                url = None
        return out

    def delete_resource(self, project_id, res):
        url = f"{BASE}/v13/deployments/{res.id}"
        try:
            r = requests.delete(url, headers=self.headers)
        except requests.RequestException as e:
            return False, f"请求异常: {e}"
        if r.status_code == 200:
            return True, None
        return False, f"[{r.status_code}] {r.text[:200]}"
