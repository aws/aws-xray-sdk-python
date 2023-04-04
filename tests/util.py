import json
import threading

from aws_xray_sdk.core.recorder import AWSXRayRecorder
from aws_xray_sdk.core.emitters.udp_emitter import UDPEmitter
from aws_xray_sdk.core.sampling.sampler import DefaultSampler
from aws_xray_sdk.core.utils.compat import PY35


class StubbedEmitter(UDPEmitter):

    def __init__(self, daemon_address='127.0.0.1:2000'):
        super().__init__(daemon_address)
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


class StubbedSampler(DefaultSampler):

    def start(self):
        pass


def get_new_stubbed_recorder():
    """
    Returns a new AWSXRayRecorder object with emitter stubbed
    """
    if not PY35:
        recorder = AWSXRayRecorder()
    else:
        from aws_xray_sdk.core.async_recorder import AsyncAWSXRayRecorder
        recorder = AsyncAWSXRayRecorder()

    recorder.configure(emitter=StubbedEmitter(), sampler=StubbedSampler())
    return recorder


def entity_to_dict(trace_entity):

    raw = json.loads(trace_entity.serialize())
    return raw


def _search_entity(entity, name):
    """Helper function to that recursivly looks at subentities
    Returns a serialized entity that matches the name given or None"""
    if 'name' in entity:
        my_name = entity['name']
        if my_name == name:
            return entity
        else:
            if "subsegments" in entity:
                for s in entity['subsegments']:
                    result = _search_entity(s, name)
                    if result is not None:
                        return result
    return None


def find_subsegment(segment, name):
    """Helper function to find a subsegment by name in the entity tree"""
    segment = entity_to_dict(segment)
    for entity in segment['subsegments']:
        result = _search_entity(entity, name)
        if result is not None:
            return result
    return None


def find_subsegment_by_annotation(segment, key, value):
    """Helper function to find a subsegment by annoation key & value in the entity tree"""
    segment = entity_to_dict(segment)
    for entity in segment['subsegments']:
        result = _search_entity_by_annotation(entity, key, value)
        if result is not None:
            return result
    return None 


def _search_entity_by_annotation(entity, key, value):
    """Helper function to that recursivly looks at subentities
    Returns a serialized entity that matches the annoation key & value given or None"""
    if 'annotations' in entity:
        if key in entity['annotations']:
            my_value = entity['annotations'][key]
            if my_value == value:
                return entity
        else:
            if "subsegments" in entity:
                for s in entity['subsegments']:
                    result = _search_entity_by_annotation(s, key, value)
                    if result is not None:
                        return result
    return None