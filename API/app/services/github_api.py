from github import Github, Auth
from app.config import settings

class GitHubAPI:
    def __init__(self):
        self.client = Github(auth=Auth.Token(settings.GITHUB_TOKEN)) if settings.GITHUB_TOKEN else Github()

    def repo(self, owner: str, repo: str):
        return self.client.get_repo(f"{owner}/{repo}")

    def get_commit(self, owner: str, repo: str, sha: str):
        return self.repo(owner, repo).get_commit(sha)

    def get_file_at_commit(self, owner: str, repo: str, path: str, sha: str) -> str:
        content = self.repo(owner, repo).get_contents(path, ref=sha)
        if isinstance(content, list):
            raise ValueError(f"{path} is a directory, not a file")
        return content.decoded_content.decode("utf-8", errors="replace")

    def get_commit_context(self, owner: str, repo: str, sha: str) -> dict:
        commit = self.get_commit(owner, repo, sha)
        return {
            "sha": commit.sha,
            "message": commit.commit.message,
            "files": [
                {"filename": f.filename, "status": f.status, "patch": f.patch}
                for f in commit.files
            ],
        }
