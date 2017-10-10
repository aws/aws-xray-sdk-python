import pytest

from aws_xray_sdk.core.models.facade_segment import FacadeSegment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.exceptions.exceptions import FacadeSegmentMutationException
from aws_xray_sdk.core.models import http


def test_not_ready():

    segment = FacadeSegment('name', 'id', 'id', True)
    segment.in_progress = False
    assert not segment.ready_to_send()


def test_initializing():

    segment = FacadeSegment('name', 'id', 'id', False)
    assert not segment.initializing

    segment2 = FacadeSegment('name', None, 'id', True)
    assert segment2.initializing


def test_unsupported_operations():

    segment = FacadeSegment('name', 'id', 'id', False)

    with pytest.raises(FacadeSegmentMutationException):
        segment.put_annotation('key', 'value')

    with pytest.raises(FacadeSegmentMutationException):
        segment.put_metadata('key', 'value')

    with pytest.raises(FacadeSegmentMutationException):
        segment.set_user('user')

    with pytest.raises(FacadeSegmentMutationException):
        segment.close()

    with pytest.raises(FacadeSegmentMutationException):
        segment.serialize()

    with pytest.raises(FacadeSegmentMutationException):
        segment.put_http_meta(http.URL, 'value')


def test_structure_intact():

    segment = FacadeSegment('name', 'id', 'id', True)
    subsegment = Subsegment('name', 'local', segment)
    subsegment2 = Subsegment('name', 'local', segment)
    segment.add_subsegment(subsegment)
    subsegment.add_subsegment(subsegment2)

    assert segment.subsegments[0] is subsegment
    assert subsegment.subsegments[0] is subsegment2
