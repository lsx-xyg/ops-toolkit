"""GitHub API 封装（基于 PyGithub）。

以后加任何 GitHub 功能都复用这里的方法。
"""
from github import Github, Auth
from github.GithubException import GithubException


class GitHubClient:
    token_env = "GITHUB_TOKEN"

    def __init__(self, token):
        self._gh = Github(auth=Auth.Token(token))

    # ---------- 通用 ----------
    def get_repo(self, full_name):
        return self._gh.get_repo(full_name)

    def list_repos(self):
        """返回 [(full_name, full_name), ...]"""
        user = self._gh.get_user()
        return [(r.full_name, r.full_name) for r in user.get_repos()]

    # ---------- Release ----------
    def list_releases(self, full_name):
        """返回 PyGithub 的 GitRelease 列表。"""
        repo = self.get_repo(full_name)
        return list(repo.get_releases())

    def delete_release(self, release_obj):
        """传 PyGithub 的 GitRelease 对象。"""
        try:
            release_obj.delete_release()
            return True, None
        except GithubException as e:
            return False, _fmt_err(e)

    def delete_tag(self, full_name, tag_name):
        try:
            repo = self.get_repo(full_name)
            ref = repo.get_git_ref(f"tags/{tag_name}")
            ref.delete()
            return True, None
        except GithubException as e:
            # 404: tag 不存在也算成功
            if e.status == 404:
                return True, None
            return False, _fmt_err(e)

    # ---------- 未来扩展点 ----------
    # def list_workflow_runs(self, full_name):
    #     return list(self.get_repo(full_name).get_workflow_runs())
    #
    # def delete_workflow_run(self, run_obj):
    #     run_obj.delete()
    #
    # def list_packages(self, org_or_user):
    #     ...


def _fmt_err(e: GithubException) -> str:
    msg = ""
    if isinstance(e.data, dict):
        msg = e.data.get("message", "")
    return f"[{e.status}] {msg or str(e)}"
