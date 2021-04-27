import os
from aws_xray_sdk.core import xray_recorder

from aws_xray_sdk.core.models.traceid import TraceId


def test_id_format():
    trace_id = TraceId().to_id()
    assert len(trace_id) == 35

    parts = trace_id.split(TraceId.DELIMITER)
    assert parts[0] == '1'
    int(parts[1], 16)
    int(parts[2], 16)


def test_id_generation_default_sampling_false():
    segment = xray_recorder.begin_segment('segment_name', sampling=False)

    # Start and end a subsegment
    subsegment = xray_recorder.begin_subsegment('subsegment_name')
    xray_recorder.end_subsegment()

    # Close the segment
    xray_recorder.end_segment()

    assert segment.id == '0000000000000000'
    assert segment.trace_id == '1-00000000-000000000000000000000000'
    assert subsegment.id == '0000000000000000'
    assert subsegment.trace_id == '1-00000000-000000000000000000000000'
    assert subsegment.parent_id == '0000000000000000'


def test_id_generation_default_sampling_true():
    segment = xray_recorder.begin_segment('segment_name', sampling=True)

    # Start and end a subsegment
    subsegment = xray_recorder.begin_subsegment('subsegment_name')
    xray_recorder.end_subsegment()

    # Close the segment
    xray_recorder.end_segment()

    assert segment.id != '0000000000000000'
    assert segment.trace_id != '1-00000000-000000000000000000000000'
    assert subsegment.id != '0000000000000000'
    assert subsegment.trace_id != '1-00000000-000000000000000000000000'
    assert subsegment.parent_id != '0000000000000000'


def test_id_generation_noop_true():
    os.environ['AWS_XRAY_NOOP_ID'] = 'True'
    segment = xray_recorder.begin_segment('segment_name', sampling=False)

    # Start and end a subsegment
    subsegment = xray_recorder.begin_subsegment('subsegment_name')
    xray_recorder.end_subsegment()

    # Close the segment
    xray_recorder.end_segment()
    os.unsetenv('AWS_XRAY_NOOP_ID')

    assert segment.id == '0000000000000000'
    assert segment.trace_id == '1-00000000-000000000000000000000000'
    assert subsegment.id == '0000000000000000'
    assert subsegment.trace_id == '1-00000000-000000000000000000000000'
    assert subsegment.parent_id == '0000000000000000'


def test_id_generation_noop_false():
    os.environ['AWS_XRAY_NOOP_ID'] = 'FALSE'
    segment = xray_recorder.begin_segment('segment_name', sampling=False)

    # Start and end a subsegment
    subsegment = xray_recorder.begin_subsegment('subsegment_name')
    xray_recorder.end_subsegment()

    # Close the segment
    xray_recorder.end_segment()
    os.unsetenv('AWS_XRAY_NOOP_ID')

    assert segment.id != '0000000000000000'
    assert segment.trace_id != '1-00000000-000000000000000000000000'
    assert subsegment.id != '0000000000000000'
    assert subsegment.trace_id != '1-00000000-000000000000000000000000'
    assert subsegment.parent_id != '0000000000000000'
