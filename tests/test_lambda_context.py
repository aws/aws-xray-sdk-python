import os

from aws_xray_sdk import global_sdk_config
import pytest
from aws_xray_sdk.core import lambda_launcher
from aws_xray_sdk.core.models.subsegment import Subsegment


TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
PARENT_ID = '53995c3f42cd8ad8'
DATA = 'Foo=Bar'
HEADER_VAR = "Root=%s;Parent=%s;Sampled=1;%s" % (TRACE_ID, PARENT_ID, DATA)

os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY] = HEADER_VAR
context = lambda_launcher.LambdaContext()


@pytest.fixture(autouse=True)
def setup():
    yield
    global_sdk_config.set_sdk_enabled(True)


def test_facade_segment_generation():

    segment = context.get_trace_entity()
    assert segment.id == PARENT_ID
    assert segment.trace_id == TRACE_ID
    assert segment.sampled
    assert DATA in segment.get_origin_trace_header().to_header_str()


def test_put_subsegment():

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
    assert DATA in subsegment2.parent_segment.get_origin_trace_header().to_header_str()

    context.end_subsegment()
    assert context.get_trace_entity().id == subsegment.id

    context.end_subsegment()
    assert context.get_trace_entity().id == segment.id


def test_disable():
    context.clear_trace_entities()
    segment = context.get_trace_entity()
    assert segment.sampled

    context.clear_trace_entities()
    global_sdk_config.set_sdk_enabled(False)
    segment = context.get_trace_entity()
    assert not segment.sampled
    assert DATA in segment.get_origin_trace_header().to_header_str()


def test_non_initialized():
    # Context that hasn't been initialized by lambda container should not add subsegments to the dummy segment.
    temp_header_var = os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY]
    del os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY]

    temp_context = lambda_launcher.LambdaContext()
    dummy_segment = temp_context.get_trace_entity()
    subsegment = Subsegment("TestSubsegment", "local", dummy_segment)
    temp_context.put_subsegment(subsegment)

    assert temp_context.get_trace_entity() == dummy_segment

    # "Lambda" container added metadata now. Should see subsegment now.
    # The following put_segment call will overwrite the dummy segment in the context with an intialized facade segment that accepts a subsegment.
    os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY] = temp_header_var
    temp_context.put_subsegment(subsegment)

    assert temp_context.get_trace_entity() == subsegment


def test_set_trace_entity():
    segment = context.get_trace_entity()
    subsegment = Subsegment('name', 'local', segment)

    context. clear_trace_entities()

    # should set the parent segment in thread local
    context.set_trace_entity(subsegment)
    tl = context._local
    assert tl.__getattribute__('segment') == segment
    assert context.get_trace_entity() == subsegment

    context.clear_trace_entities()

    # should set the segment in thread local
    context.set_trace_entity(segment)
    tl = context._local
    assert tl.__getattribute__('segment') == segment
    assert context.get_trace_entity() == segment
