import platform

import pytest

from aws_xray_sdk.version import VERSION
from .util import get_new_stubbed_recorder

import aws_xray_sdk
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models.dummy_entities import DummySegment, DummySubsegment

xray_recorder = get_new_stubbed_recorder()
XRAY_ENABLED_KEY = aws_xray_sdk.global_sdk_config.XRAY_ENABLED_KEY


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage before and after each test run.
    """
    xray_recorder.configure(sampling=False)
    xray_recorder.clear_trace_entities()
    yield
    xray_recorder.clear_trace_entities()
    aws_xray_sdk.global_sdk_config.set_sdk_enabled(True)


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


def test_put_annotation_metadata():
    segment = xray_recorder.begin_segment('name')
    xray_recorder.put_annotation('key1', 'value1')
    subsegment = xray_recorder.begin_subsegment('name')
    xray_recorder.put_metadata('key2', 'value2')

    assert 'value1' == segment.annotations['key1']
    assert not segment.annotations.get('key2')
    assert 'value2' == subsegment.metadata['default']['key2']
    assert not subsegment.metadata['default'].get('key1')


def test_pass_through_with_missing_context():

    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='LOG_ERROR')
    assert not xray_recorder.is_sampled()

    xray_recorder.put_annotation('key', 'value')
    xray_recorder.put_metadata('key', 'value')
    xray_recorder.end_segment()


def test_capture_not_suppress_exception():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='LOG_ERROR')

    @xray_recorder.capture()
    def buggy_func():
        return 1 / 0

    with pytest.raises(ZeroDivisionError):
        buggy_func()


def test_capture_not_swallow_return():
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(sampling=False, context_missing='LOG_ERROR')
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
    assert aws_xray_sdk.global_sdk_config.sdk_enabled()
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    assert type(xray_recorder.current_segment()) is Segment
    assert type(xray_recorder.current_subsegment()) is Subsegment


def test_disable_is_dummy():
    aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)
    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    assert type(xray_recorder.current_segment()) is DummySegment
    assert type(xray_recorder.current_subsegment()) is DummySubsegment
