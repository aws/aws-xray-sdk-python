# -*- coding: iso-8859-15 -*-
import pytest

from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models import http
from aws_xray_sdk.core.exceptions.exceptions import SegmentNameMissingException
from aws_xray_sdk.core.exceptions.exceptions import SegmentNotFoundException
from aws_xray_sdk.core.exceptions.exceptions import AlreadyEndedException

from .util import entity_to_dict


def test_unicode_entity_name():

    name1 = u'福'
    name2 = u'セツナ'
    segment = Segment(name1)
    subsegment = Subsegment(name2, 'local', segment)

    assert segment.name == name1
    assert subsegment.name == name2


def test_segment_user():
    segment = Segment('seg')
    segment.set_user('whoami')
    doc = entity_to_dict(segment)

    assert doc['user'] == 'whoami'


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
    segment.put_annotation('valid_key', invalid)
    segment.put_annotation('invalid-key', 'validvalue')
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


def test_no_rule_name_pollution():
    segment1 = Segment('seg1')
    segment2 = Segment('seg2')
    segment1.set_rule_name('rule1')
    segment2.set_rule_name('rule2')

    assert segment1.aws['xray']['sampling_rule_name'] == 'rule1'
    assert segment2.aws['xray']['sampling_rule_name'] == 'rule2'


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


def test_add_exception():
    segment = Segment('seg')
    exception = Exception("testException")
    stack = [['path', 'line', 'label']]
    segment.add_exception(exception=exception, stack=stack)
    segment.close()

    cause = segment.cause
    assert 'exceptions' in cause
    exceptions = cause['exceptions']
    assert len(exceptions) == 1
    assert 'working_directory' in cause
    exception = exceptions[0]
    assert 'testException' == exception.message
    expected_stack = [{'path': 'path', 'line': 'line', 'label': 'label'}]
    assert expected_stack == exception.stack


def test_add_exception_referencing():
    segment = Segment('seg')
    subseg = Subsegment('subseg', 'remote', segment)
    exception = Exception("testException")
    stack = [['path', 'line', 'label']]
    subseg.add_exception(exception=exception, stack=stack)
    segment.add_exception(exception=exception, stack=stack)
    subseg.close()
    segment.close()

    seg_cause = segment.cause
    subseg_cause = subseg.cause

    assert isinstance(subseg_cause, dict)
    assert isinstance(seg_cause, str)
    assert seg_cause == subseg_cause['exceptions'][0].id


def test_add_exception_cause_resetting():
    segment = Segment('seg')
    subseg = Subsegment('subseg', 'remote', segment)
    exception = Exception("testException")
    stack = [['path', 'line', 'label']]
    subseg.add_exception(exception=exception, stack=stack)
    segment.add_exception(exception=exception, stack=stack)

    segment.add_exception(exception=Exception("newException"), stack=stack)
    subseg.close()
    segment.close()

    seg_cause = segment.cause
    assert isinstance(seg_cause, dict)
    assert 'newException' == seg_cause['exceptions'][0].message


def test_add_exception_appending_exceptions():
    segment = Segment('seg')
    stack = [['path', 'line', 'label']]
    segment.add_exception(exception=Exception("testException"), stack=stack)
    segment.add_exception(exception=Exception("newException"), stack=stack)
    segment.close()

    assert isinstance(segment.cause, dict)
    assert len(segment.cause['exceptions']) == 2
