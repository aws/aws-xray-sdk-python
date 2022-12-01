import platform
import time

import pytest

from aws_xray_sdk.core.sampling.sampling_rule import SamplingRule
from aws_xray_sdk.core.sampling.rule_cache import RuleCache
from aws_xray_sdk.core.sampling.sampler import DefaultSampler
from aws_xray_sdk.version import VERSION
from .util import get_new_stubbed_recorder

from aws_xray_sdk import global_sdk_config
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models.dummy_entities import DummySegment, DummySubsegment
from aws_xray_sdk.core.exceptions.exceptions import SegmentNotFoundException

xray_recorder = get_new_stubbed_recorder()


@pytest.fixture(autouse=True)
def construct_ctx(monkeypatch):
    """
    Clean up context storage before and after each test run.
    """
    monkeypatch.delattr("botocore.session.Session.get_credentials")
    xray_recorder.configure(sampling=False)
    xray_recorder.clear_trace_entities()
    yield
    xray_recorder.clear_trace_entities()
    global_sdk_config.set_sdk_enabled(True)


def test_default_runtime_context():
    segment = xray_recorder.begin_segment('name')
    xray_meta = segment.aws.get('xray')
    assert 'X-Ray for Python' == xray_meta.get('sdk')
    assert VERSION == xray_meta.get('sdk_version')

    service = segment.service
    assert platform.python_implementation() == service.get('runtime')
    assert platform.python_version() == service.get('runtime_version')


def test_subsegment_parenting():
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    xray_recorder.end_subsegment('name')
    assert xray_recorder.get_trace_entity() is segment

    subsegment1 = xray_recorder.begin_subsegment('name1')
    subsegment2 = xray_recorder.begin_subsegment('name2')

    assert subsegment2.parent_id == subsegment1.id
    assert subsegment1.parent_id == segment.id
    assert subsegment.parent_id == xray_recorder.current_segment().id

    xray_recorder.end_subsegment()
    assert not subsegment2.in_progress
    assert subsegment1.in_progress
    assert xray_recorder.current_subsegment().id == subsegment1.id

    xray_recorder.end_subsegment()
    assert not subsegment1.in_progress
    assert xray_recorder.get_trace_entity() is segment


def test_subsegments_streaming():
    xray_recorder.configure(streaming_threshold=10)
    segment = xray_recorder.begin_segment('name')
    for i in range(0, 11):
        xray_recorder.begin_subsegment(name=str(i))
    for i in range(0, 1):
        # subsegment '10' will be streamed out upon close
        xray_recorder.end_subsegment()

    assert segment.get_total_subsegments_size() == 10
    assert xray_recorder.current_subsegment().name == '9'


def test_subsegment_streaming_set_zero():
    xray_recorder.configure(streaming_threshold=0)
    segment = xray_recorder.begin_segment('name')
    xray_recorder.begin_subsegment(name='sub')
    xray_recorder.end_subsegment()

    assert xray_recorder.streaming.streaming_threshold == 0
    assert segment.get_total_subsegments_size() == 0


def test_put_annotation_metadata():
    segment = xray_recorder.begin_segment('name')
    xray_recorder.put_annotation('key1', 'value1')
    subsegment = xray_recorder.begin_subsegment('name')
    xray_recorder.put_metadata('key2', 'value2')

    assert 'value1' == segment.annotations['key1']
    assert not segment.annotations.get('key2')
    assert 'value2' == subsegment.metadata['default']['key2']
    assert not subsegment.metadata['default'].get('key1')


def test_default_pass_through_with_missing_context():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False) # default context_missing = 'LOG_ERROR'
    assert not xray_recorder.is_sampled()

    xray_recorder.put_annotation('key', 'value')
    xray_recorder.put_metadata('key', 'value')
    xray_recorder.end_segment()

def test_raise_runtime_error_with_missing_context():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='RUNTIME_ERROR')

    with pytest.raises(SegmentNotFoundException):
        assert not xray_recorder.is_sampled()
        xray_recorder.end_segment()

def test_capture_not_suppress_exception():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False)

    @xray_recorder.capture()
    def buggy_func():
        return 1 / 0

    with pytest.raises(ZeroDivisionError):
        buggy_func()


def test_capture_not_swallow_return():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False)
    value = 1

    @xray_recorder.capture()
    def my_func():
        return value

    actual = my_func()
    assert actual == value


def test_first_begin_segment_sampled():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=True)
    segment = xray_recorder.begin_segment('name')

    assert segment.sampled

def test_unsampled_subsegment_of_sampled_parent():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=True)
    segment = xray_recorder.begin_segment('name', sampling=True)
    subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled')

    assert segment.sampled == True
    assert subsegment.sampled == False

def test_begin_subsegment_unsampled():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False)
    segment = xray_recorder.begin_segment('name', sampling=False)
    subsegment = xray_recorder.begin_subsegment_without_sampling('unsampled')

    assert segment.sampled == False
    assert subsegment.sampled == False


def test_in_segment_closing():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False)

    with xray_recorder.in_segment('name') as segment:
        assert segment.in_progress is True
        segment.put_metadata('key1', 'value1')
        segment.put_annotation('key2', 'value2')
        with xray_recorder.in_subsegment('subsegment') as subsegment:
            assert subsegment.in_progress is True

        with xray_recorder.capture('capture') as subsegment:
            assert subsegment.in_progress is True
            assert subsegment.name == 'capture'

    assert subsegment.in_progress is False
    assert segment.in_progress is False
    assert segment.annotations['key2'] == 'value2'
    assert segment.metadata['default']['key1'] == 'value1'


def test_in_segment_exception():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False)

    with pytest.raises(Exception):
        with xray_recorder.in_segment('name') as segment:
            assert segment.in_progress is True
            assert 'exceptions' not in segment.cause
            raise Exception('test exception')

    assert segment.in_progress is False
    assert segment.fault is True
    assert len(segment.cause['exceptions']) == 1

    with pytest.raises(Exception):
        with xray_recorder.in_segment('name') as segment:
            with xray_recorder.in_subsegment('name') as subsegment:
                    assert subsegment.in_progress is True
                    raise Exception('test exception')

    assert len(subsegment.cause['exceptions']) == 1


def test_default_enabled():
    assert global_sdk_config.sdk_enabled()
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    assert type(xray_recorder.current_segment()) is Segment
    assert type(xray_recorder.current_subsegment()) is Subsegment


def test_disable_is_dummy():
    global_sdk_config.set_sdk_enabled(False)
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    assert type(xray_recorder.current_segment()) is DummySegment
    assert type(xray_recorder.current_subsegment()) is DummySubsegment

def test_unsampled_subsegment_is_dummy():
    assert global_sdk_config.sdk_enabled()
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment_without_sampling('name')
    
    assert type(xray_recorder.current_subsegment()) is DummySubsegment

def test_subsegment_respects_parent_sampling_decision():
    assert global_sdk_config.sdk_enabled()
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment_without_sampling('name2')
    subsegment2 = xray_recorder.begin_subsegment('unsampled-subsegment')

    assert type(xray_recorder.current_subsegment()) is DummySubsegment
    assert subsegment.sampled == False
    assert subsegment2.sampled == False


def test_disabled_empty_context_current_calls():
    global_sdk_config.set_sdk_enabled(False)
    assert type(xray_recorder.current_segment()) is DummySegment
    assert type(xray_recorder.current_subsegment()) is DummySubsegment


def test_disabled_out_of_order_begins():
    global_sdk_config.set_sdk_enabled(False)
    xray_recorder.begin_subsegment("Test")
    xray_recorder.begin_segment("Test")
    xray_recorder.begin_subsegment("Test1")
    xray_recorder.begin_subsegment("Test2")
    assert type(xray_recorder.begin_subsegment("Test3")) is DummySubsegment
    assert type(xray_recorder.begin_segment("Test4")) is DummySegment


def test_disabled_put_methods():
    global_sdk_config.set_sdk_enabled(False)
    xray_recorder.put_annotation("Test", "Value")
    xray_recorder.put_metadata("Test", "Value", "Namespace")


# Test for random end segments/subsegments without any entities in context.
# Should not throw any exceptions
def test_disabled_ends():
    global_sdk_config.set_sdk_enabled(False)
    xray_recorder.end_segment()
    xray_recorder.end_subsegment()
    xray_recorder.end_segment()
    xray_recorder.end_segment()
    xray_recorder.end_subsegment()
    xray_recorder.end_subsegment()


# Begin subsegment should not fail on its own.
def test_disabled_begin_subsegment():
    global_sdk_config.set_sdk_enabled(False)
    subsegment_entity = xray_recorder.begin_subsegment("Test")
    assert type(subsegment_entity) is DummySubsegment


# When disabled, force sampling should still return dummy entities.
def test_disabled_force_sampling():
    global_sdk_config.set_sdk_enabled(False)
    xray_recorder.configure(sampling=True)
    segment_entity = xray_recorder.begin_segment("Test1")
    subsegment_entity = xray_recorder.begin_subsegment("Test2")
    assert type(segment_entity) is DummySegment
    assert type(subsegment_entity) is DummySubsegment


# When disabled, get_trace_entity should return DummySegment if an entity is not present in the context
def test_disabled_get_context_entity():
    global_sdk_config.set_sdk_enabled(False)
    entity = xray_recorder.get_trace_entity()
    assert type(entity) is DummySegment


def test_max_stack_trace_zero():
    xray_recorder.configure(max_trace_back=1)
    with pytest.raises(Exception):
        with xray_recorder.in_segment('name') as segment_with_stack:
            assert segment_with_stack.in_progress is True
            assert 'exceptions' not in segment_with_stack.cause.__dict__
            raise Exception('Test Exception')
    assert len(segment_with_stack.cause['exceptions']) == 1

    xray_recorder.configure(max_trace_back=0)
    with pytest.raises(Exception):
        with xray_recorder.in_segment('name') as segment_no_stack:
            assert segment_no_stack.in_progress is True
            assert 'exceptions' not in segment_no_stack.cause.__dict__
            raise Exception('Test Exception')
    assert len(segment_no_stack.cause['exceptions']) == 1

    assert len(segment_with_stack.cause['exceptions'][0].stack) == 1
    assert len(segment_no_stack.cause['exceptions'][0].stack) == 0


# CustomSampler to mimic the DefaultSampler,
# but without the rule and target polling logic.
class CustomSampler(DefaultSampler):
    def start(self):
        pass

    def should_trace(self, sampling_req=None):
        rule_cache = RuleCache()
        rule_cache.last_updated = int(time.time())
        sampling_rule_a = SamplingRule(name='rule_a',
                                       priority=2,
                                       rate=0.5,
                                       reservoir_size=1,
                                       service='app_a')
        sampling_rule_b = SamplingRule(name='rule_b',
                                       priority=2,
                                       rate=0.5,
                                       reservoir_size=1,
                                       service='app_b')
        rule_cache.load_rules([sampling_rule_a, sampling_rule_b])
        now = int(time.time())
        if sampling_req and not sampling_req.get('service_type', None):
            sampling_req['service_type'] = self._origin
        elif sampling_req is None:
            sampling_req = {'service_type': self._origin}
        matched_rule = rule_cache.get_matched_rule(sampling_req, now)
        if matched_rule:
            return self._process_matched_rule(matched_rule, now)
        else:
            return self._local_sampler.should_trace(sampling_req)


def test_begin_segment_matches_sampling_rule_on_name():
    xray_recorder.configure(sampling=True, sampler=CustomSampler())
    segment = xray_recorder.begin_segment("app_b")
    assert segment.aws.get('xray').get('sampling_rule_name') == 'rule_b'
