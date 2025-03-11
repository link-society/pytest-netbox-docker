from datetime import timedelta
import secrets

import pytest

from docker.models.networks import Network
from docker.models.containers import Container
from docker import DockerClient
import docker

from .utils import td_to_ns, wait_for_healthcheck, HealthcheckFailed
from . import settings


@pytest.fixture(scope=settings.SCOPE)
def netbox_docker_client():
    client = docker.from_env()

    reclaimable = client.containers.list(
        filters={"label": "org.pytest.plugin=netbox-docker"},
        all=True,
    )

    for container in reclaimable:
        container.remove(force=True)

    reclaimable = client.networks.list(
        filters={"label": "org.pytest.plugin=netbox-docker"},
    )

    for network in reclaimable:
        network.remove()

    return client


@pytest.fixture(scope=settings.SCOPE)
def netbox_docker_network(netbox_docker_client: DockerClient):
    network = netbox_docker_client.networks.create(
        "pytest-netbox-docker",
        labels={"org.pytest.plugin": "netbox-docker"},
    )

    yield network

    network.remove()


@pytest.fixture(scope=settings.SCOPE)
def netbox_database_password():
    return secrets.token_hex(16)


@pytest.fixture(scope=settings.SCOPE)
def netbox_queue_password():
    return secrets.token_hex(16)


@pytest.fixture(scope=settings.SCOPE)
def netbox_cache_password():
    return secrets.token_hex(16)


@pytest.fixture(scope=settings.SCOPE)
def netbox_database(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_database_password: str,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.POSTGRES_IMAGE,
        name="pytest-netbox-database",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment={
            "POSTGRES_DB": "netbox",
            "POSTGRES_USER": "netbox",
            "POSTGRES_PASSWORD": netbox_database_password,
        },
        network=netbox_docker_network.name,
        healthcheck={
            "test": "pg_isready -q -t 2 -d netbox -U netbox",
            "start_period": td_to_ns(timedelta(seconds=20)),
            "interval": td_to_ns(timedelta(seconds=1)),
            "timeout": td_to_ns(timedelta(seconds=5)),
            "retries": 5,
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox_queue(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_queue_password: str,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.VALKEY_IMAGE,
        name="pytest-netbox-queue",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment={
            "REDIS_PASSWORD": netbox_queue_password,
        },
        network=netbox_docker_network.name,
        command=[
            "/bin/sh",
            "-c",
            'valkey-server --save "" --appendonly no --requirepass "${REDIS_PASSWORD}"',
        ],
        healthcheck={
            "test": '[ $(valkey-cli --pass "${REDIS_PASSWORD}" ping) == "PONG" ]',
            "start_period": td_to_ns(timedelta(seconds=5)),
            "interval": td_to_ns(timedelta(seconds=1)),
            "timeout": td_to_ns(timedelta(seconds=3)),
            "retries": 5,
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox_cache(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_cache_password: str,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.VALKEY_IMAGE,
        name="pytest-netbox-cache",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment={
            "REDIS_PASSWORD": netbox_cache_password,
        },
        network=netbox_docker_network.name,
        command=[
            "/bin/sh",
            "-c",
            'valkey-server --save "" --appendonly no --requirepass "${REDIS_PASSWORD}"',
        ],
        healthcheck={
            "test": '[ $(valkey-cli --pass "${REDIS_PASSWORD}" ping) == "PONG" ]',
            "start_period": td_to_ns(timedelta(seconds=5)),
            "interval": td_to_ns(timedelta(seconds=1)),
            "timeout": td_to_ns(timedelta(seconds=3)),
            "retries": 5,
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox_env(
    netbox_database_password: str,
    netbox_queue_password: str,
    netbox_cache_password: str,
):
    return {
        "CORS_ORIGIN_ALLOW_ALL": "True",

        "DB_HOST": "pytest-netbox-database",
        "DB_NAME": "netbox",
        "DB_USER": "netbox",
        "DB_PASSWORD": netbox_database_password,

        "EMAIL_FROM": "netbox@bar.com",
        "EMAIL_SERVER": "localhost",
        "EMAIL_PORT": "25",
        "EMAIL_SSL_CERTFILE": "",
        "EMAIL_SSL_KEYFILE": "",
        "EMAIL_TIMEOUT": "5",
        "EMAIL_USERNAME": "",
        "EMAIL_PASSWORD": "",
        "EMAIL_USE_SSL": "false",
        "EMAIL_USE_TLS": "false",

        "REDIS_CACHE_DATABASE": "1",
        "REDIS_CACHE_HOST": "pytest-netbox-cache",
        "REDIS_CACHE_INSECURE_SKIP_TLS_VERIFY": "false",
        "REDIS_CACHE_PASSWORD": netbox_cache_password,
        "REDIS_CACHE_SSL": "false",

        "REDIS_DATABASE": "0",
        "REDIS_HOST": "pytest-netbox-queue",
        "REDIS_PASSWORD": netbox_queue_password,
        "REDIS_INSECURE_SKIP_TLS_VERIFY": "false",
        "REDIS_SSL": "false",

        "GRAPHQL_ENABLED": "true",
        "METRICS_ENABLED": "false",
        "WEBHOOKS_ENABLED": "true",

        "SECRET_KEY": secrets.token_hex(64),

        "MEDIA_ROOT": "/opt/netbox/netbox/media",
        "HOUSEKEEPING_INTERVAL": "86400",
        "SKIP_SUPERUSER": "false",
        "RELEASE_CHECK_URL": "https://api.github.com/repos/netbox-community/netbox/releases",
    }


@pytest.fixture(scope=settings.SCOPE)
def netbox_rqworker(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_env: dict[str, str],
    netbox_database: Container,
    netbox_queue: Container,
    netbox_cache: Container,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.NETBOX_IMAGE,
        name="pytest-netbox-rqworker",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment=netbox_env,
        network=netbox_docker_network.name,
        user="unit:root",
        command=[
            "/opt/netbox/venv/bin/python",
            "/opt/netbox/netbox/manage.py",
            "rqworker",
        ],
        healthcheck={
            "test": "ps -aux | grep -v grep | grep -q rqworker || exit 1",
            "start_period": td_to_ns(timedelta(seconds=settings.NETBOX_START_PERIOD)),
            "timeout": td_to_ns(timedelta(seconds=3)),
            "interval": td_to_ns(timedelta(seconds=15)),
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox_housekeeping(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_env: dict[str, str],
    netbox_database: Container,
    netbox_queue: Container,
    netbox_cache: Container,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.NETBOX_IMAGE,
        name="pytest-netbox-housekeeping",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment=netbox_env,
        network=netbox_docker_network.name,
        user="unit:root",
        command="/opt/netbox/housekeeping.sh",
        healthcheck={
            "test": "ps -aux | grep -v grep | grep -q housekeeping || exit 1",
            "start_period": td_to_ns(timedelta(seconds=settings.NETBOX_START_PERIOD)),
            "timeout": td_to_ns(timedelta(seconds=3)),
            "interval": td_to_ns(timedelta(seconds=15)),
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox_webserver(
    netbox_docker_client: DockerClient,
    netbox_docker_network: Network,
    netbox_env: dict[str, str],
    netbox_database: Container,
    netbox_queue: Container,
    netbox_cache: Container,
):
    container: Container = netbox_docker_client.containers.run(
        image=settings.NETBOX_IMAGE,
        name="pytest-netbox-webserver",
        labels={"org.pytest.plugin": "netbox-docker"},
        environment=netbox_env,
        network=netbox_docker_network.name,
        ports={"8080/tcp": ('127.0.0.1', 8080)},
        user="unit:root",
        healthcheck={
            "test": "curl -f http://localhost:8080/login/ || exit 1",
            "start_period": td_to_ns(timedelta(seconds=settings.NETBOX_START_PERIOD)),
            "timeout": td_to_ns(timedelta(seconds=3)),
            "interval": td_to_ns(timedelta(seconds=15)),
        },
        detach=True,
    )

    try:
        wait_for_healthcheck(container)
        yield container

    except HealthcheckFailed:
        print(container.logs().decode())
        raise

    finally:
        container.stop()
        container.remove(force=True)


@pytest.fixture(scope=settings.SCOPE)
def netbox(
    netbox_webserver: Container,
    netbox_rqworker: Container,
    netbox_housekeeping: Container,
):
    exit_code, _ = netbox_webserver.exec_run(
        cmd=[
            "/opt/netbox/venv/bin/python",
            "/opt/netbox/netbox/manage.py",
            "migrate"
        ]
    )
    assert exit_code == 0
