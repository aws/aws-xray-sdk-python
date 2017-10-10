import os
import socket
import logging

from ..exceptions.exceptions import InvalidDaemonAddressException

log = logging.getLogger(__name__)


PROTOCOL_HEADER = "{\"format\": \"json\", \"version\": 1}"
PROTOCOL_DELIMITER = '\n'
DAEMON_ADDRESS_KEY = "AWS_XRAY_DAEMON_ADDRESS"


class UDPEmitter(object):
    """
    The default emitter the X-Ray recorder uses to send segments/subsegments
    to the X-Ray daemon over UDP using a non-blocking socket. If there is an
    exception on the actual data transfer between the socket and the daemon,
    it logs the exception and continue.
    """
    def __init__(self, daemon_address='127.0.0.1:2000'):

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        address = os.getenv(DAEMON_ADDRESS_KEY, daemon_address)
        self._ip, self._port = self._parse_address(address)

    def send_entity(self, entity):
        """
        Serializes a segment/subsegment and sends it to the X-Ray daemon
        over UDP. By default it doesn't retry on failures.

        :param entity: a trace entity to send to the X-Ray daemon
        """
        message = "%s%s%s" % (PROTOCOL_HEADER,
                              PROTOCOL_DELIMITER,
                              entity.serialize())

        log.debug("sending: %s to %s:%s." % (message, self._ip, self._port))
        self._send_data(message)

    def set_daemon_address(self, address):
        """
        Takes a full address like 127.0.0.1:2000 and parses it into ip address
        and port. Throws an exception if the address has invalid format.
        """
        if address:
            self._ip, self._port = self._parse_address(address)

    def _send_data(self, data):

        try:
            self._socket.sendto(data.encode('utf-8'), (self._ip,
                                self._port))
        except Exception:
            log.exception('failed to send data to X-Ray daemon.')

    def _parse_address(self, daemon_address):
        try:
            val = daemon_address.split(':')
            return val[0], int(val[1])
        except Exception:
            raise InvalidDaemonAddressException('Invalid daemon address %s specified.' % daemon_address)
