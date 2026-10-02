import docker
from app.config import settings

class DockerRunner:
    def __init__(self):
        self.client = docker.from_env()

    def run(self, workspace: str, command: str):
        container = self.client.containers.run(
            image=settings.DOCKER_IMAGE,
            command=["/bin/sh", "-lc", command],
            volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            network_disabled=True,
            mem_limit="2g",
            cpu_quota=50000,
            detach=True,
            user="10001:10001",
        )
        try:
            result = container.wait(timeout=settings.DOCKER_TIMEOUT)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            return {"status": result.get("StatusCode"), "logs": logs}
        finally:
            container.remove(force=True)
