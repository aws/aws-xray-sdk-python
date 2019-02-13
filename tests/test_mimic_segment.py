import pytest

from aws_xray_sdk.core.models.facade_segment import FacadeSegment
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models.mimic_segment import MimicSegment
from aws_xray_sdk.core.exceptions.exceptions import MimicSegmentInvalidException


original_segment = Segment("RealSegment")
facade_segment = FacadeSegment("FacadeSegment", "entityid", "traceid", True)


@pytest.fixture(autouse=True)
def cleanup_ctx():
    global original_segment, facade_segment
    original_segment = Segment("RealSegment")
    facade_segment = FacadeSegment("FacadeSegment", "entityid", "traceid", True)
    yield
    original_segment = Segment("RealSegment")
    facade_segment = FacadeSegment("FacadeSegment", "entityid", "traceid", True)


def test_ready():
    mimic_segment = MimicSegment(facade_segment=facade_segment, original_segment=original_segment)
    mimic_segment.in_progress = False
    assert mimic_segment.ready_to_send()


def test_invalid_init():
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=None, original_segment=original_segment)
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=facade_segment, original_segment=None)
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=Subsegment("Test", "local", original_segment), original_segment=None)
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=None, original_segment=Subsegment("Test", "local", original_segment))
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=facade_segment, original_segment=Subsegment("Test", "local", original_segment))
    with pytest.raises(MimicSegmentInvalidException):
        MimicSegment(facade_segment=original_segment, original_segment=facade_segment)
    MimicSegment(facade_segment=facade_segment, original_segment=original_segment)


def test_init_similar():
    mimic_segment = MimicSegment(facade_segment=facade_segment, original_segment=original_segment)  # type: MimicSegment

    assert mimic_segment.id == original_segment.id
    assert mimic_segment.name == original_segment.name
    assert mimic_segment.in_progress == original_segment.in_progress

    assert mimic_segment.trace_id == facade_segment.trace_id
    assert mimic_segment.parent_id == facade_segment.id
    assert mimic_segment.sampled == facade_segment.sampled

    mimic_segment_serialized = mimic_segment.__getstate__()
    assert mimic_segment_serialized['namespace'] == "local"
    assert mimic_segment_serialized['type'] == "subsegment"


def test_facade_segment_properties():
    # Sampling decision is made by Facade Segment
    original_segment.sampled = False
    facade_segment.sampled = True
    mimic_segment = MimicSegment(facade_segment=facade_segment, original_segment=original_segment)  # type: MimicSegment

    assert mimic_segment.sampled == facade_segment.sampled
    assert mimic_segment.sampled != original_segment.sampled


def test_segment_methods_on_mimic():
    # Test to make sure that segment methods exist and function for the Mimic Segment
    mimic_segment = MimicSegment(facade_segment=facade_segment, original_segment=original_segment)  # type: MimicSegment
    assert not getattr(mimic_segment, "service", None)
    assert not getattr(mimic_segment, "user", None)
    assert getattr(mimic_segment, "ref_counter", None)
    assert getattr(mimic_segment, "_subsegments_counter", None)

    assert not getattr(original_segment, "service", None)
    assert not getattr(original_segment, "user", None)
    assert getattr(original_segment, "ref_counter", None)
    assert getattr(original_segment, "_subsegments_counter", None)

    mimic_segment.set_service("SomeService")
    original_segment.set_service("SomeService")
    assert original_segment.service == original_segment.service

    assert original_segment.get_origin_trace_header() == mimic_segment.get_origin_trace_header()
    mimic_segment.save_origin_trace_header("someheader")
    original_segment.save_origin_trace_header("someheader")
    assert original_segment.get_origin_trace_header() == mimic_segment.get_origin_trace_header()

    # No exception is thrown
    test_dict = {"akey": "avalue"}
    original_segment.set_aws(test_dict)
    original_segment.set_rule_name(test_dict)
    original_segment.set_user("SomeUser")
    mimic_segment.set_aws(test_dict)
    mimic_segment.set_rule_name(test_dict)
    mimic_segment.set_user("SomeUser")
