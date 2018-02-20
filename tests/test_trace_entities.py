import pytest

from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models import http
from aws_xray_sdk.core.exceptions.exceptions import SegmentNameMissingException
from aws_xray_sdk.core.exceptions.exceptions import SegmentNotFoundException
from aws_xray_sdk.core.exceptions.exceptions import AlreadyEndedException

from .util import entity_to_dict


def test_put_http_meta():

    segment = Segment('seg')
    segment.put_http_meta(http.URL, 'my url')
    segment.put_http_meta(http.STATUS, 200)
    # unsupported key should be dropped
    segment.put_http_meta('somekey', 'somevalue')

    doc = entity_to_dict(segment)
    assert doc['http']['request'][http.URL] == 'my url'
    assert doc['http']['response'][http.STATUS] == 200
    assert 'somekey' not in doc


def test_put_metadata():

    segment = Segment('seg')
    meta = {
        'key1': 'value1',
        'key2': 'value2',
    }
    segment.put_metadata('key', meta)

    subsegment = Subsegment('sub', 'local', segment)
    segment.add_subsegment(subsegment)
    subsegment.put_metadata('key', meta, 'my namespace')

    doc = entity_to_dict(segment)
    assert doc['metadata']['default']['key'] == meta

    sub_doc = doc['subsegments'][0]
    assert sub_doc['metadata']['my namespace']['key'] == meta


def test_put_annotation():

    segment = Segment('seg')
    invalid = {
        'key1': 'value1',
        'key2': 'value2',
    }
    # invalid annotation key-value pair should be dropped
    segment.put_annotation('invalid_value', invalid)
    segment.put_annotation('invalid-key', invalid)
    segment.put_annotation('number', 1)

    subsegment = Subsegment('sub', 'local', segment)
    segment.add_subsegment(subsegment)
    subsegment.put_annotation('bool', False)

    doc = entity_to_dict(segment)
    assert doc['annotations']['number'] == 1
    assert 'invalid-value' not in doc['annotations']
    assert 'invalid-key' not in doc['annotations']

    sub_doc = doc['subsegments'][0]
    assert not sub_doc['annotations']['bool']


def test_reference_counting():

    segment = Segment('seg')
    subsegment = Subsegment('sub', 'local', segment)
    segment.add_subsegment(subsegment)
    subsegment = Subsegment('sub', 'local', segment)
    subsubsegment = Subsegment('subsub', 'local', segment)
    subsegment.add_subsegment(subsubsegment)

    assert not segment.ready_to_send()
    assert segment.ref_counter.get_current() == 2

    subsubsegment.close()
    assert not segment.ready_to_send()
    assert segment.ref_counter.get_current() == 1

    subsegment.close()
    assert not segment.ready_to_send()
    assert segment.ref_counter.get_current() == 0

    segment.close()
    assert segment.ready_to_send()
    assert segment.get_total_subsegments_size() == 2


def test_flags_on_status_code():

    segment1 = Segment('seg')
    segment1.apply_status_code(429)
    assert segment1.throttle
    assert segment1.error

    segment2 = Segment('seg')
    segment2.apply_status_code(503)
    assert segment2.fault

    segment3 = Segment('seg')
    segment3.apply_status_code(403)
    assert segment3.error


def test_mutate_closed_entity():

    segment = Segment('seg')
    segment.close()

    with pytest.raises(AlreadyEndedException):
        segment.put_annotation('key', 'value')

    with pytest.raises(AlreadyEndedException):
        segment.put_metadata('key', 'value')

    with pytest.raises(AlreadyEndedException):
        segment.put_http_meta('url', 'my url')

    with pytest.raises(AlreadyEndedException):
        segment.close()


def test_no_empty_properties():

    segment = Segment('seg')
    segment.close()
    doc = entity_to_dict(segment)

    assert 'http' not in doc
    assert 'aws' not in doc
    assert 'metadata' not in doc
    assert 'annotations' not in doc
    assert 'subsegments' not in doc
    assert 'cause' not in doc


def test_required_properties():

    segment = Segment('seg')
    segment.close()
    doc = entity_to_dict(segment)

    assert 'trace_id' in doc
    assert 'id' in doc
    assert 'start_time' in doc
    assert 'end_time' in doc


def test_missing_segment_name():

    with pytest.raises(SegmentNameMissingException):
        Segment(None)


def test_missing_parent_segment():

    with pytest.raises(SegmentNotFoundException):
        Subsegment('name', 'local', None)
