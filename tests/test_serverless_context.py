import os
import pytest

from aws_xray_sdk.core import serverless_context
from aws_xray_sdk.core import context
from aws_xray_sdk.core.lambda_launcher import LAMBDA_TRACE_HEADER_KEY
from aws_xray_sdk.core.exceptions.exceptions import AlreadyEndedException, SegmentNotFoundException
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
from aws_xray_sdk.core.models.mimic_segment import MimicSegment
from aws_xray_sdk.core.models.facade_segment import FacadeSegment


TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
PARENT_ID = '53995c3f42cd8ad8'
HEADER_VAR = "Root=%s;Parent=%s;Sampled=1" % (TRACE_ID, PARENT_ID)

os.environ[LAMBDA_TRACE_HEADER_KEY] = HEADER_VAR
context = serverless_context.ServerlessContext()

service_name = "Test Flask Server"


@pytest.fixture(autouse=True)
def cleanup_ctx():
    context.clear_trace_entities()
    yield
    context.clear_trace_entities()


def test_segment_generation():
    # Ensure we create Mimic Segments, and that parents of Mimic segments are Facade Segments.
    segment = Segment(service_name)
    context.put_segment(segment)

    mimic_segment = context.get_trace_entity()
    assert type(mimic_segment) == MimicSegment

    facade_segment = getattr(context._local, 'segment', None)
    assert type(facade_segment) == FacadeSegment
    assert mimic_segment.parent_id == facade_segment.id

    assert facade_segment.id == PARENT_ID
    assert facade_segment.trace_id == TRACE_ID
    assert facade_segment.sampled


def test_facade_in_threadlocal():
    # Ensure that facade segments are stored in threadlocal.segment
    assert not getattr(context._local, 'segment', None)

    # Refresh context to generate the facade segment.
    context._refresh_context()
    facade_segment = getattr(context._local, 'segment', None)
    assert facade_segment
    assert type(facade_segment) == FacadeSegment
    assert facade_segment.id == PARENT_ID
    assert facade_segment.trace_id == TRACE_ID


def test_put_subsegment():
    segment = Segment(service_name)
    context.put_segment(segment)

    segment = context.get_trace_entity()
    subsegment = Subsegment('name', 'local', segment)
    context.put_subsegment(subsegment)
    assert context.get_trace_entity().id == subsegment.id

    subsegment2 = Subsegment('name', 'local', segment)
    context.put_subsegment(subsegment2)
    assert context.get_trace_entity().id == subsegment2.id

    assert subsegment.subsegments[0] is subsegment2
    assert subsegment2.parent_id == subsegment.id
    assert subsegment.parent_id == segment.id
    assert subsegment2.parent_segment is segment

    assert context.get_trace_entity().id == subsegment2.id

    context.end_subsegment()
    assert context.get_trace_entity().id == subsegment.id

    context.end_subsegment()
    assert context.get_trace_entity().id == segment.id
    assert context.get_trace_entity().in_progress

    context.end_segment()
    assert context.get_trace_entity().id == segment.id
    assert not context.get_trace_entity().in_progress


def test_remote_mimic_segment():
    # Ensure that the mimic-generated segment is set as a subsegment
    # when being serialized through jsonpickle (which uses .__getstate__())
    segment = Segment(service_name)
    context.put_segment(segment)

    mimic_segment = context.get_trace_entity()

    segment_properties = mimic_segment.__getstate__()
    assert segment_properties['namespace'] == "local"
    assert segment_properties['type'] == "subsegment"


def test_segment_methods_on_mimic_segment():
    # Ensure that segment operations made on the mimic segment all works.
    comparison_segment = Segment(service_name)  # type: Segment
    context.put_segment(comparison_segment)
    mimic_segment = context.get_trace_entity()  # type: MimicSegment

    trace_header = "Someheader"
    comparison_segment.save_origin_trace_header(trace_header)
    mimic_segment.save_origin_trace_header(trace_header)
    assert mimic_segment.get_origin_trace_header() == comparison_segment.get_origin_trace_header()

    assert mimic_segment.get_total_subsegments_size() == comparison_segment.get_total_subsegments_size()
    comparison_segment.increment()
    mimic_segment.increment()
    assert mimic_segment.get_total_subsegments_size() == comparison_segment.get_total_subsegments_size()

    comparison_segment.decrement_subsegments_size()
    assert mimic_segment.get_total_subsegments_size() != comparison_segment.get_total_subsegments_size()
    mimic_segment.decrement_subsegments_size()
    assert mimic_segment.get_total_subsegments_size() == comparison_segment.get_total_subsegments_size()

    assert mimic_segment.ready_to_send() == comparison_segment.ready_to_send()


def test_empty_context():
    # Test to make sure an touched context is absolutely clear.
    # Call to get_trace_entity should produce a facade segment.
    assert not context._local.__dict__

    # Empty context should throw an exception
    with pytest.raises(SegmentNotFoundException):
        context.get_trace_entity()

    # Induce the creation of a facade segment by putting in a segment.
    assert len(context._local.__dict__) == 0
    segment = Segment(service_name)
    context.put_segment(segment)

    assert type(context._local.segment) == FacadeSegment
    assert len(context._local.entities) == 1


def test_set_trace_entity():
    segment_one = Segment(service_name)
    context.put_segment(segment_one)
    first_mimic_segment = context.get_trace_entity()
    facade_segment = getattr(context._local, 'segment', None)

    segment_two = Segment("WOOH")
    context.set_trace_entity(segment_two)
    second_mimic_segment = context.get_trace_entity()

    assert first_mimic_segment.id == segment_one.id
    assert first_mimic_segment.name == segment_one.name
    assert first_mimic_segment.parent_id == facade_segment.id
    assert first_mimic_segment.trace_id == facade_segment.trace_id
    assert second_mimic_segment.id == segment_two.id
    assert second_mimic_segment.name == segment_two.name
    assert second_mimic_segment.parent_id == facade_segment.id
    assert second_mimic_segment.trace_id == facade_segment.trace_id


def test_segment_close_subsegment_open():
    # Tests to make sure that when the parent, mimic segment is closed,
    # and the last entity is a subsegment, the segment itself closes.
    segment = Segment(service_name)
    context.put_segment(segment)
    mimic_segment = context.get_trace_entity()
    assert mimic_segment.in_progress
    subsegment = Subsegment("test", "local", mimic_segment)
    context.put_subsegment(subsegment)
    context.end_segment()
    assert not mimic_segment.in_progress


def test_begin_close_twice():
    segment_one = Segment(service_name)
    context.put_segment(segment_one)
    context.end_segment()
    entity_one = context.get_trace_entity()
    context.put_segment(segment_one)
    context.end_segment()
    entity_two = context.get_trace_entity()
    assert entity_one != entity_two


def test_cant_end_segment_twice():
    segment_one = Segment(service_name)
    context.put_segment(segment_one)
    context.end_segment()
    with pytest.raises(AlreadyEndedException):
        context.end_segment()
