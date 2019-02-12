import os

from aws_xray_sdk import global_sdk_config
import pytest
from aws_xray_sdk.core import lambda_launcher
from aws_xray_sdk.core.models.subsegment import Subsegment


TRACE_ID = '1-5759e988-bd862e3fe1be46a994272793'
PARENT_ID = '53995c3f42cd8ad8'
HEADER_VAR = "Root=%s;Parent=%s;Sampled=1" % (TRACE_ID, PARENT_ID)

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


def test_non_initialized():
    # Context that hasn't been initialized by lambda container should not add subsegments to the facade segment.
    temp_header_var = os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY]
    del os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY]

    temp_context = lambda_launcher.LambdaContext()
    facade_segment = temp_context.get_trace_entity()
    subsegment = Subsegment("TestSubsegment", "local", facade_segment)
    temp_context.put_subsegment(subsegment)

    assert temp_context.get_trace_entity() == facade_segment

    # "Lambda" container added metadata now. Should see subsegment now.
    os.environ[lambda_launcher.LAMBDA_TRACE_HEADER_KEY] = temp_header_var
    temp_context.put_subsegment(subsegment)

    assert temp_context.get_trace_entity() == subsegment
