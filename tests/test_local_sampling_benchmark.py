import json
import pkgutil
from pkg_resources import resource_filename

from aws_xray_sdk.core.sampling.local.sampler import LocalSampler

def test_pkg_resources_static_read(benchmark):
    def get_sampling_rule():
        with open(resource_filename(__name__, 'mock_sampling_rule.json')) as f:
            return json.load(f)
    benchmark(get_sampling_rule)

def test_pkgutil_static_read(benchmark):
    def get_sampling_rule():
        json.loads(pkgutil.get_data(__name__, 'mock_sampling_rule.json'))
    benchmark(get_sampling_rule)
