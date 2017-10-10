from aws_xray_sdk.core.models.dummy_entities import DummySegment, DummySubsegment
from aws_xray_sdk.core.models import http


def test_not_sampled():

    segment = DummySegment()
    subsegment = DummySubsegment(segment)

    assert not segment.sampled
    assert not subsegment.sampled


def test_no_ops():

    segment = DummySegment()
    segment.put_metadata('key', 'value')
    segment.put_annotation('key', 'value')
    segment.put_http_meta(http.URL, 'url')
    segment.set_user('user')

    assert not segment.metadata
    assert not segment.annotations
    assert not segment.http
    assert not segment.user

    subsegment = DummySubsegment(segment)
    subsegment.put_metadata('key', 'value')
    subsegment.put_annotation('key', 'value')
    subsegment.put_http_meta(http.URL, 'url')
    subsegment.set_user('user')
    subsegment.set_aws({'key': 'value'})
    subsegment.set_sql({'key': 'value'})

    assert not subsegment.metadata
    assert not subsegment.annotations
    assert not subsegment.http
    assert not subsegment.user
    assert not subsegment.aws
    assert not subsegment.sql

    assert not segment.serialize()
    assert not subsegment.serialize()


def test_structure_intact():
    segment = DummySegment()
    subsegment = DummySubsegment(segment)
    subsegment2 = DummySubsegment(segment)
    subsegment.add_subsegment(subsegment2)
    segment.add_subsegment(subsegment)

    assert segment.subsegments[0] is subsegment
    assert subsegment.subsegments[0] is subsegment2

    subsegment2.close()
    subsegment.close()
    segment.close()
    assert segment.ready_to_send()
