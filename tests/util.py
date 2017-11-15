import json
import threading

from aws_xray_sdk.core.recorder import AWSXRayRecorder
from aws_xray_sdk.core.emitters.udp_emitter import UDPEmitter
from aws_xray_sdk.core.utils.compat import PY35


class StubbedEmitter(UDPEmitter):

    def __init__(self, daemon_address='127.0.0.1:2000'):
        super(StubbedEmitter, self).__init__(daemon_address)
        self._local = threading.local()

    def send_entity(self, entity):
        setattr(self._local, 'cache', entity)

    def pop(self):
        if hasattr(self._local, 'cache'):
            entity = self._local.cache
        else:
            entity = None

        self._local.__dict__.clear()
        return entity


def get_new_stubbed_recorder():
    """
    Returns a new AWSXRayRecorder object with emitter stubbed
    """
    if not PY35:
        recorder = AWSXRayRecorder()
    else:
        from aws_xray_sdk.core.async_recorder import AsyncAWSXRayRecorder
        recorder = AsyncAWSXRayRecorder()

    recorder.emitter = StubbedEmitter()
    return recorder


def entity_to_dict(trace_entity):

    raw = json.loads(trace_entity.serialize())
    return raw
