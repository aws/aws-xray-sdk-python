import platform

from .util import get_new_stubbed_recorder
from aws_xray_sdk.version import VERSION
from aws_xray_sdk.core.async_context import AsyncContext
import asyncio


xray_recorder = get_new_stubbed_recorder()


@xray_recorder.capture_async('test_2')
async def async_method2():
    pass


@xray_recorder.capture_async('test_1')
async def async_method():
    await async_method2()


async def test_capture(event_loop):
    xray_recorder.configure(
        service='test', sampling=False, context=AsyncContext(loop=event_loop)
    )

    segment = xray_recorder.begin_segment('name')

    await async_method()

    # Check subsegment is created from async_method
    assert len(segment.subsegments) == 1
    assert segment.subsegments[0].name == 'test_1'

    # Check nested subsegment is created from async_method2
    subsegment = segment.subsegments[0]
    assert len(subsegment.subsegments) == 1
    assert subsegment.subsegments[0].name == 'test_2'

    # Check runtime context is correctly attached
    xray_meta = segment.aws.get('xray')
    assert 'X-Ray for Python' == xray_meta.get('sdk')
    assert VERSION == xray_meta.get('sdk_version')

    service = segment.service
    assert platform.python_implementation() == service.get('runtime')
    assert platform.python_version() == service.get('runtime_version')

async def test_concurrent_calls(event_loop):
    xray_recorder.configure(
        service='test', sampling=False, context=AsyncContext(loop=event_loop)
    )
    async with xray_recorder.in_segment_async('segment') as segment:
        global counter
        counter = 0
        total_tasks = 10
        flag = asyncio.Event()
        async def assert_task():
            async with xray_recorder.in_subsegment_async('segment') as subsegment:
                global counter
                counter += 1
                # Begin all subsegments before closing any to ensure they overlap
                if counter < total_tasks:
                    await flag.wait()
                else:
                    flag.set()
                return subsegment.parent_id
        tasks = [assert_task() for task in range(total_tasks)]
        subsegs_parent_ids = await asyncio.gather(*tasks)
        for subseg_parent_id in subsegs_parent_ids:
            assert subseg_parent_id == segment.id


async def test_async_context_managers(event_loop):
    xray_recorder.configure(
        service='test', sampling=False, context=AsyncContext(loop=event_loop)
    )

    async with xray_recorder.in_segment_async('segment') as segment:
        async with xray_recorder.capture_async('aio_capture') as subsegment:
            assert segment.subsegments[0].name == 'aio_capture'
        assert subsegment.in_progress is  False
        async with xray_recorder.in_subsegment_async('in_sub') as subsegment:
            assert segment.subsegments[1].name == 'in_sub'
            assert subsegment.in_progress is  True
        assert subsegment.in_progress is  False
