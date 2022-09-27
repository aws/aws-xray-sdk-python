import httpx

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core.models import http
from aws_xray_sdk.ext.util import UNKNOWN_HOSTNAME, inject_trace_header


def patch():
    httpx.Client = _InstrumentedClient
    httpx.AsyncClient = _InstrumentedAsyncClient
    httpx._api.Client = _InstrumentedClient


class _InstrumentedClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._original_transport = self._transport
        self._transport = SyncInstrumentedTransport(self._transport)


class _InstrumentedAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._original_transport = self._transport
        self._transport = AsyncInstrumentedTransport(self._transport)


class SyncInstrumentedTransport(httpx.BaseTransport):
    def __init__(self, transport: httpx.BaseTransport):
        self._wrapped_transport = transport

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        def httpx_processor(return_value, exception, subsegment, stack, **kwargs):
            subsegment.put_http_meta(http.METHOD, request.method)
            subsegment.put_http_meta(
                http.URL,
                str(request.url.copy_with(password=None, query=None, fragment=None)),
            )

            if return_value is not None:
                subsegment.put_http_meta(http.STATUS, return_value.status_code)
            elif exception:
                subsegment.add_exception(exception, stack)

        inject_trace_header(request.headers, xray_recorder.current_subsegment())
        return xray_recorder.record_subsegment(
            wrapped=self._wrapped_transport.handle_request,
            instance=self._wrapped_transport,
            args=(request,),
            kwargs={},
            name=request.url.host or UNKNOWN_HOSTNAME,
            namespace="remote",
            meta_processor=httpx_processor,
        )


class AsyncInstrumentedTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport):
        self._wrapped_transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        def httpx_processor(return_value, exception, subsegment, stack, **kwargs):
            subsegment.put_http_meta(http.METHOD, request.method)
            subsegment.put_http_meta(
                http.URL,
                str(request.url.copy_with(password=None, query=None, fragment=None)),
            )

            if return_value is not None:
                subsegment.put_http_meta(http.STATUS, return_value.status_code)
            elif exception:
                subsegment.add_exception(exception, stack)

        inject_trace_header(request.headers, xray_recorder.current_subsegment())
        return await xray_recorder.record_subsegment_async(
            wrapped=self._wrapped_transport.handle_async_request,
            instance=self._wrapped_transport,
            args=(request,),
            kwargs={},
            name=request.url.host or UNKNOWN_HOSTNAME,
            namespace="remote",
            meta_processor=httpx_processor,
        )
