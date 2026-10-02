from app.services.github_api import GitHubAPI

def git_analysis(state):
    ctx = GitHubAPI().get_commit_context(state["owner"], state["repo"], state["commit"])
    return {"git_context": ctx}
