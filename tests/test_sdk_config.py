from aws_xray_sdk.sdk_config import SDKConfig
import os
import pytest


XRAY_ENABLED_KEY = "AWS_XRAY_ENABLED"


@pytest.fixture(autouse=True)
def cleanup():
    """
    Clean up Environmental Variable for enable before and after tests
    """
    if XRAY_ENABLED_KEY in os.environ:
        del os.environ[XRAY_ENABLED_KEY]
    yield
    if XRAY_ENABLED_KEY in os.environ:
        del os.environ[XRAY_ENABLED_KEY]


def test_enable_key():
    assert SDKConfig.XRAY_ENABLED_KEY == XRAY_ENABLED_KEY


def test_default_enabled():
    assert SDKConfig.sdk_enabled() is True


def test_env_var_precedence():
    os.environ[XRAY_ENABLED_KEY] = "true"
    SDKConfig.set_sdk_enabled(False)
    assert SDKConfig.sdk_enabled() is True
    os.environ[XRAY_ENABLED_KEY] = "false"
    SDKConfig.set_sdk_enabled(False)
    assert SDKConfig.sdk_enabled() is False
    os.environ[XRAY_ENABLED_KEY] = "false"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is False
    os.environ[XRAY_ENABLED_KEY] = "true"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is True
    os.environ[XRAY_ENABLED_KEY] = "true"
    SDKConfig.set_sdk_enabled(None)
    assert SDKConfig.sdk_enabled() is True


def test_env_enable_case():
    os.environ[XRAY_ENABLED_KEY] = "TrUE"
    SDKConfig.set_sdk_enabled(True)  # Env Variable takes precedence. This is called to activate the internal check
    assert SDKConfig.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "true"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "False"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is False

    os.environ[XRAY_ENABLED_KEY] = "falSE"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is False


def test_invalid_env_string():
    os.environ[XRAY_ENABLED_KEY] = "INVALID"
    SDKConfig.set_sdk_enabled(True)  # Env Variable takes precedence. This is called to activate the internal check
    assert SDKConfig.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "1.0"
    SDKConfig.set_sdk_enabled(True)
    assert SDKConfig.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "1-.0"
    SDKConfig.set_sdk_enabled(False)
    assert SDKConfig.sdk_enabled() is True
