import logging

log = logging.getLogger(__name__)

ROOT = 'Root'
PARENT = 'Parent'
SAMPLE = 'Sampled'

HEADER_DELIMITER = ";"


class TraceHeader(object):
    """
    The sampling decision and trace ID are added to HTTP requests in
    tracing headers named ``X-Amzn-Trace-Id``. The first X-Ray-integrated
    service that the request hits adds a tracing header, which is read
    by the X-Ray SDK and included in the response. Learn more about
    `Tracing Header <http://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html#xray-concepts-tracingheader>`_.
    """
    def __init__(self, root=None, parent=None, sampled=None):
        """
        :param str root: trace id
        :param str parent: parent id
        :param int sampled: 0 means not sampled, 1 means sampled
        """
        self._root = root
        self._parent = parent
        self._sampled = None

        if sampled is not None:
            self._sampled = int(sampled)

    @classmethod
    def from_header_str(cls, header):
        """
        Create a TraceHeader object from a tracing header string
        extracted from a http request headers.
        """
        if not header:
            return cls()

        try:
            params = header.strip().split(HEADER_DELIMITER)
            header_dict = {}

            for param in params:
                entry = param.split('=')
                header_dict[entry[0]] = entry[1]

            return cls(
                root=header_dict.get(ROOT, None),
                parent=header_dict.get(PARENT, None),
                sampled=header_dict.get(SAMPLE, None),
            )

        except Exception:
            log.warning("malformed tracing header %s, ignore.", header)
            return cls()

    def to_header_str(self):
        """
        Convert to a tracing header string that can be injected to
        outgoing http request headers.
        """
        h_str = ''
        if self.root:
            h_str = ROOT + '=' + self.root
        if self.parent:
            h_str = h_str + HEADER_DELIMITER + PARENT + '=' + self.parent
        if self.sampled is not None:
            h_str = h_str + HEADER_DELIMITER + SAMPLE + '=' + str(self.sampled)

        return h_str

    @property
    def root(self):
        """
        Return trace id of the header
        """
        return self._root

    @property
    def parent(self):
        """
        Return the parent segment id in the header
        """
        return self._parent

    @property
    def sampled(self):
        """
        Return the sampling decision in the header.
        It's either 0 or 1.
        """
        return self._sampled
