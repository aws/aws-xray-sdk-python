from aws_xray_sdk.core.models.segment import Segment

def test_create_segment():
    segment = Segment('test')
    assert segment.name == 'test'
