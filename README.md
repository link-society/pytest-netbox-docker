# Pytest Netbox Docker

Pytest plugin that provides fixtures to start a complete Netbox infrastructure
using Docker.

It does not use [testcontainers](https://testcontainers.com/) because it is a
thin wrapper around the Python Docker SDK, and it does not expose the required
features.

## :package: Installation

```bash
pip install git+https://github.com/link-society/pytest-netbox-docker.git
```

## :hammer: Usage

> :warning: **Important Notice**
>
> The Netbox webserver container will expose the port 8080 on 127.0.0.1,
> therefore this port should be free when running the test suite.

First, write a test that uses the `netbox` fixture:

```python
def test_mytest(netbox):
  resp = requests.get("http://localhost:8080/login/")
  resp.raise_for_status()
```

Then run your test suite with the plugin activated:

```bash
pytest -p pytest_netbox_docker
```

> **NB:** Netbox can take a long time to start (and apply the migrations).

## :wrench: Configuration

| Environment Variable | Default Value | Description |
| --- | --- | --- |
| `PYTEST_NETBOX_PLUGIN_SCOPE` | `session` | Scope of the fixtures for the test suite |
| `PYTEST_NETBOX_PLUGIN_POSTGRES_IMAGE` | `docker.io/postgres:17-alpine` | Docker image to use for Netbox's database |
| `PYTEST_NETBOX_PLUGIN_VALKEY_IMAGE` | `docker.io/valkey/valkey:8.0-alpine` | Docker image to use for Netbox's cache and queue |
| `PYTEST_NETBOX_PLUGIN_NETBOX_IMAGE` | `docker.io/netboxcommunity/netbox:latest` | Docker image to use for Netbox itself |
| `PYTEST_NETBOX_PLUGIN_NETBOX_START_PERIOD` | `120` | Duration (in seconds) to wait for Netbox to start before considering the container "unhealthy" |

## :memo: License

This project is released under the terms of the [MIT License](./LICENSE.txt)
