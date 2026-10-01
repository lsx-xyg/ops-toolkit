"""统一的 HTTP 封装。"""
import requests


class ApiError(Exception):
    pass


def build_headers(token, prefix="Bearer", extra=None):
    h = {"Authorization": f"{prefix} {token}"}
    if extra:
        h.update(extra)
    return h


def get_json(url, headers, params=None):
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code in (401, 403):
        raise ApiError(f"认证失败或权限不足 [{resp.status_code}] {resp.text[:200]}")
    resp.raise_for_status()
    return resp.json()
