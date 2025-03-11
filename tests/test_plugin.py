import pytest


@pytest.mark.usefixtures("netbox")
def test_plugin():
    assert True
