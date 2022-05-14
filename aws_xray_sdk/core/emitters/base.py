import logging
from abc import ABCMeta, abstractmethod

from .constants import (
    DEFAULT_DAEMON_ADDRESS,
    PROTOCOL_DELIMITER,
    PROTOCOL_HEADER,
)
from ..exceptions.exceptions import InvalidDaemonAddressException

log = logging.getLogger(__name__)


class Emitter(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, daemon_address=DEFAULT_DAEMON_ADDRESS):
        pass

    def send_entity(self, entity):
        """
        Serializes a segment/subsegment and sends it to the X-Ray daemon.

        :param entity: a trace entity to send to the X-Ray daemon
        """
        try:
            message = "%s%s%s" % (PROTOCOL_HEADER,
                                  PROTOCOL_DELIMITER,
                                  entity.serialize())

            log.debug("sending: %s to %s:%s." % (message, self._ip, self._port))
            self._send_data(message)
        except Exception:
            log.exception("Failed to send entity to Daemon.")

    @abstractmethod
    def set_daemon_address(self, address):
        """
        Set up ip and port from the raw daemon address.
        """
        pass

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def _send_data(self, data):
        self._socket.sendto(data.encode('utf-8'), (self._ip, self._port))

    def _parse_address(self, daemon_address):
        try:
            val = daemon_address.split(':')
            return val[0], int(val[1])
        except Exception:
            raise InvalidDaemonAddressException('Invalid daemon address %s specified.' % daemon_address)
