from aws_xray_sdk.core.models.traceid import TraceId


def test_id_format():
    trace_id = TraceId().to_id()
    assert len(trace_id) == 35

    parts = trace_id.split(TraceId.DELIMITER)
    assert parts[0] == '1'
    int(parts[1], 16)
    int(parts[2], 16)
