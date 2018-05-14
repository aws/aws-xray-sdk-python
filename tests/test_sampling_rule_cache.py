import time
import pytest

from aws_xray_sdk.core.sampling.sampling_rule import SamplingRule
from aws_xray_sdk.core.sampling.rule_cache import RuleCache
from aws_xray_sdk.core.sampling.reservoir import Reservoir

rule_0 = SamplingRule(name='a', priority=1, rate=0.1,
                      reservoir_size=1, host='*mydomain*',
                      method='GET', path='myop', service='random',
                      service_type='random')
rule_1 = SamplingRule(name='aa', priority=2, rate=0.1,
                      reservoir_size=1, host='*random*',
                      method='POST', path='random', service='proxy',
                      service_type='random')
rule_2 = SamplingRule(name='b', priority=2, rate=0.1,
                      reservoir_size=1, host='*', method='GET',
                      path='ping', service='myapp',
                      service_type='AWS::EC2::Instance')
rule_default = SamplingRule(name='Default', priority=1000, rate=0.1,
                            reservoir_size=1)


@pytest.fixture(autouse=True)
def reset_rules():
    """
    Clean up context storage before and after each test run.
    """
    rules = [rule_default, rule_2, rule_0, rule_1]
    for rule in rules:
        rule.snapshot_statistics()
        rule.reservoir = Reservoir()
    yield


def test_rules_sorting():
    cache = RuleCache()
    rules = [rule_default, rule_2, rule_0, rule_1]
    cache.load_rules(rules)
    sorted_rules = cache.rules

    assert sorted_rules[0] == rule_0
    assert sorted_rules[1] == rule_1
    assert sorted_rules[2] == rule_2
    assert sorted_rules[3] == rule_default


def test_evict_deleted_rules():
    cache = RuleCache()
    cache.load_rules([rule_default, rule_1, rule_0])
    cache.load_rules([rule_default, rule_2])

    assert len(cache.rules) == 2
    assert rule_1 not in cache.rules
    assert rule_0 not in cache.rules


def test_rule_matching():
    cache = RuleCache()
    now = int(time.time())
    cache.load_rules([rule_default, rule_1, rule_2, rule_0])
    cache.last_updated = now

    sampling_req = {'host': 'mydomain.com'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.name == 'a'

    sampling_req = {'method': 'POST'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.name == 'aa'

    sampling_req = {'path': 'ping'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.name == 'b'

    sampling_req = {'service': 'proxy'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.name == 'aa'

    sampling_req = {'service_type': 'AWS::EC2::Instance'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.name == 'b'

    # Default should be always returned when there is no match
    sampling_req = {'host': 'unknown', 'path': 'unknown'}
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.is_default()


def test_preserving_sampling_statistics():
    cache = RuleCache()
    cache.load_rules([rule_default, rule_0])
    rule_0.increment_request_count()
    rule_0.increment_sampled_count()
    rule_0.reservoir.load_quota(quota=3, TTL=15, interval=None)

    new_rule_0 = SamplingRule(name='a', priority=1,
                              rate=0.1, reservoir_size=1)
    cache.load_rules([rule_default, new_rule_0])

    statistics = cache.rules[0].snapshot_statistics()
    reservoir = cache.rules[0].reservoir

    assert statistics['request_count'] == 1
    assert statistics['sampled_count'] == 1
    assert reservoir.quota == 3
    assert reservoir.TTL == 15


def test_correct_target_mapping():
    cache = RuleCache()
    cache.load_rules([rule_default, rule_0])
    targets = {
        'a': {'quota': 3, 'TTL': None, 'interval': None, 'rate': 0.1},
        'b': {'quota': 2, 'TTL': None, 'interval': None, 'rate': 0.1},
        'Default': {'quota': 5, 'TTL': None, 'interval': None, 'rate': 0.1},
    }
    cache.load_targets(targets)

    assert rule_0.reservoir.quota == 3
    assert rule_default.reservoir.quota == 5


def test_expired_cache():
    cache = RuleCache()
    now = int(time.time())
    cache.load_rules([rule_default, rule_1, rule_2, rule_0])
    cache.last_updated = now - 60 * 60 * 24  # makes rule cache one day before

    sampling_req = {'host': 'myhost.com', 'method': 'GET',
                    'path': 'operation', 'service': 'app'}

    rule = cache.get_matched_rule(sampling_req, now)
    assert rule is None

    cache.last_updated = now
    rule = cache.get_matched_rule(sampling_req, now)
    assert rule.is_default()
