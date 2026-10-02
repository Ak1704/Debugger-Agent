from app.services.github_api import GitHubAPI
from app.services.vector_store import CodeVectorStore

class CodeRetriever:
    def __init__(self):
        self.github = GitHubAPI()
        self.vectors = CodeVectorStore()

    def retrieve_file(self, owner, repo, commit, path):
        source = self.github.get_file_at_commit(owner, repo, path, commit)
        return [{"path": path, "source": source, "commit": commit}]

    def search_index(self, query, n_results=5):
        return self.vectors.search(query, n_results=n_results)
