import json
import pkgutil
from pathlib import Path

# Faster
def test_pkgutil_static_read(benchmark):
    def get_sampling_rule():
        return json.loads(pkgutil.get_data(__name__, 'mock_sampling_rule.json').decode('utf-8'))
    benchmark(get_sampling_rule)

# Slower
def test_pathlib_static_read(benchmark):
    def get_sampling_rule():
        with open(Path(__file__).parent / 'mock_sampling_rule.json') as f:
            return json.load(f)
    benchmark(get_sampling_rule)
