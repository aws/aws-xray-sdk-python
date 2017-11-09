from .reservoir import Reservoir
from ..utils.search_pattern import wildcard_match
from ..exceptions.exceptions import InvalidSamplingManifestError


class SamplingRule(object):
    """
    One SamolingRule represents one rule defined from rule json file
    or from a dictionary. It can be either a custom rule or default rule.
    """
    FIXED_TARGET = 'fixed_target'
    RATE = 'rate'

    SERVICE_NAME = 'service_name'
    METHOD = 'http_method'
    PATH = 'url_path'

    def __init__(self, rule_dict, default=False):
        """
        :param dict rule_dict: The dictionary that defines a single rule.
        :param bool default: Indicates if this is the default rule. A default
            rule cannot have `service_name`, `http_method` or `url_path`.
        """
        self._fixed_target = rule_dict.get(self.FIXED_TARGET, None)
        self._rate = rule_dict.get(self.RATE, None)

        self._service_name = rule_dict.get(self.SERVICE_NAME, None)
        self._method = rule_dict.get(self.METHOD, None)
        self._path = rule_dict.get(self.PATH, None)

        self._default = default

        self._validate()

        self._reservoir = Reservoir(self.fixed_target)

    def applies(self, service_name, method, path):
        """
        Determines whether or not this sampling rule applies to
        the incoming request based on some of the request's parameters.
        Any None parameters provided will be considered an implicit match.
        """
        return (not service_name or wildcard_match(self.service_name, service_name)) \
            and (not method or wildcard_match(self.service_name, method)) \
            and (not path or wildcard_match(self.path, path))

    @property
    def fixed_target(self):
        """
        Defines fixed number of sampled segments per second.
        This doesn't count for sampling rate.
        """
        return self._fixed_target

    @property
    def rate(self):
        """
        A float number less than 1.0 defines the sampling rate.
        """
        return self._rate

    @property
    def service_name(self):
        """
        The host name of the reqest to sample.
        """
        return self._service_name

    @property
    def method(self):
        """
        HTTP method of the request to sample.
        """
        return self._method

    @property
    def path(self):
        """
        The url path of the request to sample.
        """
        return self._path

    @property
    def reservoir(self):
        """
        Keeps track of used sampled targets within the second.
        """
        return self._reservoir

    def _validate(self):
        if self.fixed_target < 0 or self.rate < 0:
            raise InvalidSamplingManifestError('All rules must have non-negative values for '
                                               'fixed_target and rate')

        if self._default:
            if self.service_name or self.method or self.path:
                raise InvalidSamplingManifestError('The default rule must not specify values for '
                                                   'url_path, service_name, or http_method')
        else:
            if not self.service_name or not self.method or not self.path:
                raise InvalidSamplingManifestError('All non-default rules must have values for '
                                                   'url_path, service_name, and http_method')
