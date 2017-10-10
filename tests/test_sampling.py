import copy
import pytest

from aws_xray_sdk.core.sampling.sampling_rule import SamplingRule
from aws_xray_sdk.core.sampling.default_sampler import DefaultSampler
from aws_xray_sdk.core.exceptions.exceptions import InvalidSamplingManifestError


RULE = {"description": "Player moves.",
        "service_name": "*",
        "http_method": "*",
        "url_path": "/api/move/*",
        "fixed_target": 0,
        "rate": 0.05
        }


RULE_MANIFEST = {
    "version": 1,
    "rules": [{
        "description": "Player moves.",
        "service_name": "*",
        "http_method": "*",
        "url_path": "/api/move/*",
        "fixed_target": 0,
        "rate": 0
    }],
    "default": {
        "fixed_target": 1,
        "rate": 1
    }
}


def test_should_trace():

    sampler = DefaultSampler(RULE_MANIFEST)
    assert sampler.should_trace(None, 'GET', '/view')
    assert not sampler.should_trace('name', 'method', '/api/move/left')


def test_missing_version_num():

    rule = copy.deepcopy(RULE_MANIFEST)
    del rule['version']
    with pytest.raises(InvalidSamplingManifestError):
        DefaultSampler(rule)


def test_path_matching():

    rule = SamplingRule(RULE)
    assert rule.applies('name', 'GET', '/api/move/up')
    assert rule.applies(None, 'POST', '/api/move/up')
    assert rule.applies('name', None, '/api/move/up')
    assert rule.applies('name', 'PUT', None)
    assert not rule.applies(None, 'GET', '/root')


def test_negative_rate():

    rule = copy.deepcopy(RULE)
    rule['rate'] = -1
    with pytest.raises(InvalidSamplingManifestError):
        SamplingRule(rule)


def test_negative_fixed_target():

    rule = copy.deepcopy(RULE)
    rule['fixed_target'] = -1
    with pytest.raises(InvalidSamplingManifestError):
        SamplingRule(rule)


def test_invalid_default():

    with pytest.raises(InvalidSamplingManifestError):
        SamplingRule(RULE, default=True)


def test_incomplete_path_rule():

    rule = copy.deepcopy(RULE)
    del rule['url_path']
    with pytest.raises(InvalidSamplingManifestError):
        SamplingRule(rule)
