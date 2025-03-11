from datetime import timedelta
from time import sleep

from docker.models.containers import Container


class HealthcheckFailed(Exception):
    def __init__(self, container: Container):
        super().__init__(f"Container {container.name} healthcheck failed")


def td_to_ns(td: timedelta) -> int:
    return int(td.total_seconds() * 1_000_000_000)


def wait_for_healthcheck(container: Container):
    while True:
        container.reload()
        if container.health == "healthy":
            break

        elif container.health == "unhealthy":
            raise HealthcheckFailed(container)

        sleep(1)
