import pytest

from aws_xray_sdk.core.daemon_config import DaemonConfig
from aws_xray_sdk.core.exceptions.exceptions import InvalidDaemonAddressException


DEFAULT_IP = '127.0.0.1'
DEFAULT_PORT = 2000


def test_default_config():
    config = DaemonConfig()

    assert config.udp_ip == DEFAULT_IP
    assert config.tcp_ip == DEFAULT_IP
    assert config.udp_port == 2000
    assert config.tcp_port == 2000


def test_single_address():

    config = DaemonConfig('192.168.0.1:3000')

    assert config.udp_ip == '192.168.0.1'
    assert config.tcp_ip == '192.168.0.1'
    assert config.udp_port == 3000
    assert config.tcp_port == 3000


def test_set_tcp_udp_separately():

    config = DaemonConfig('tcp:192.168.0.1:3000 udp:127.0.0.2:8080')

    assert config.udp_ip == '127.0.0.2'
    assert config.tcp_ip == '192.168.0.1'
    assert config.udp_port == 8080
    assert config.tcp_port == 3000

    # order can be reversed
    config = DaemonConfig('udp:127.0.0.2:8080 tcp:192.168.0.1:3000')

    assert config.udp_ip == '127.0.0.2'
    assert config.tcp_ip == '192.168.0.1'
    assert config.udp_port == 8080
    assert config.tcp_port == 3000


def test_invalid_address():
    with pytest.raises(InvalidDaemonAddressException):
        DaemonConfig('192.168.0.1')

    with pytest.raises(InvalidDaemonAddressException):
        DaemonConfig('tcp:192.168.0.1:3000')

    with pytest.raises(InvalidDaemonAddressException):
        DaemonConfig('127.0.0.2:8080 192.168.0.1:3000')

    with pytest.raises(InvalidDaemonAddressException):
        DaemonConfig('udp:127.0.0.2:8080 192.168.0.1:3000')
