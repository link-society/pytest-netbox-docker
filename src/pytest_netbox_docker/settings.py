from decouple import config


SCOPE = config(
    "PYTEST_NETBOX_PLUGIN_SCOPE",
    default="session",
)

POSTGRES_IMAGE = config(
    "PYTEST_NETBOX_PLUGIN_POSTGRES_IMAGE",
    default="docker.io/postgres:17-alpine",
)

VALKEY_IMAGE = config(
    "PYTEST_NETBOX_PLUGIN_VALKEY_IMAGE",
    default="docker.io/valkey/valkey:8.0-alpine",
)

NETBOX_IMAGE = config(
    "PYTEST_NETBOX_PLUGIN_NETBOX_IMAGE",
    default="docker.io/netboxcommunity/netbox:latest",
)

NETBOX_START_PERIOD = config(
    "PYTEST_NETBOX_PLUGIN_NETBOX_START_PERIOD",
    default="120",
    cast=int,
)
