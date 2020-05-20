from aws_xray_sdk import global_sdk_config
import os
import pytest


XRAY_ENABLED_KEY = "AWS_XRAY_SDK_ENABLED"


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
    global_sdk_config.set_sdk_enabled(True)


def test_enable_key():
    assert global_sdk_config.XRAY_ENABLED_KEY == XRAY_ENABLED_KEY


def test_default_enabled():
    assert global_sdk_config.sdk_enabled() is True


def test_env_var_precedence():
    os.environ[XRAY_ENABLED_KEY] = "true"
    # Env Variable takes precedence. This is called to activate the internal check
    global_sdk_config.set_sdk_enabled(False)
    assert global_sdk_config.sdk_enabled() is True
    os.environ[XRAY_ENABLED_KEY] = "false"
    global_sdk_config.set_sdk_enabled(False)
    assert global_sdk_config.sdk_enabled() is False
    os.environ[XRAY_ENABLED_KEY] = "false"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is False
    os.environ[XRAY_ENABLED_KEY] = "true"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True
    os.environ[XRAY_ENABLED_KEY] = "true"
    global_sdk_config.set_sdk_enabled(None)
    assert global_sdk_config.sdk_enabled() is True


def test_env_enable_case():
    os.environ[XRAY_ENABLED_KEY] = "TrUE"
    # Env Variable takes precedence. This is called to activate the internal check
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "true"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "1"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "y"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "t"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "False"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is False

    os.environ[XRAY_ENABLED_KEY] = "falSE"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is False

    os.environ[XRAY_ENABLED_KEY] = "0"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is False


def test_invalid_env_string():
    os.environ[XRAY_ENABLED_KEY] = "INVALID"
    # Env Variable takes precedence. This is called to activate the internal check
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "1.0"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "1-.0"
    global_sdk_config.set_sdk_enabled(False)
    assert global_sdk_config.sdk_enabled() is True

    os.environ[XRAY_ENABLED_KEY] = "T RUE"
    global_sdk_config.set_sdk_enabled(True)
    assert global_sdk_config.sdk_enabled() is True
