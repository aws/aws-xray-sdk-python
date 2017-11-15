from .util import get_new_stubbed_recorder
from aws_xray_sdk.core.async_context import AsyncContext


xray_recorder = get_new_stubbed_recorder()


@xray_recorder.capture_async('test_2')
async def async_method2():
    pass


@xray_recorder.capture_async('test_1')
async def async_method():
    await async_method2()


async def test_capture(loop):
    xray_recorder.configure(service='test', sampling=False, context=AsyncContext(loop=loop))

    segment = xray_recorder.begin_segment('name')

    await async_method()

    # Check subsegment is created from async_method
    assert len(segment.subsegments) == 1
    assert segment.subsegments[0].name == 'test_1'

    # Check nested subsegment is created from async_method2
    subsegment = segment.subsegments[0]
    assert len(subsegment.subsegments) == 1
    assert subsegment.subsegments[0].name == 'test_2'
