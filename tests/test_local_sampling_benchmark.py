import json
import pkgutil
from pkg_resources import resource_filename

# Faster
def test_pkgutil_static_read(benchmark):
    def get_sampling_rule():
        # `.decode('utf-8')` needed for Python 3.4, 3.5
        return json.loads(pkgutil.get_data(__name__, 'mock_sampling_rule.json').decode('utf-8'))
    benchmark(get_sampling_rule)

# Slower
def test_pkg_resources_static_read(benchmark):
    def get_sampling_rule():
        with open(resource_filename(__name__, 'mock_sampling_rule.json')) as f:
            return json.load(f)
    benchmark(get_sampling_rule)
