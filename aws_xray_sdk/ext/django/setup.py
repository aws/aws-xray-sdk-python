import logging

import django

from aws_xray_sdk.core import xray_recorder

log = logging.getLogger(__name__)


def patch_setup():
    """
    Patch setup so that we have a mock segment during startup
    """
    attr = '_xray_original_setup'

    if getattr(django, attr, None):
        log.debug("already patched")
        return

    setattr(django, attr, setup)

    def xray_setup(*args, **kwargs):
        with xray_recorder.in_segment('setup'):
            return django._xray_original_setup(*args, **kwargs)

    django.setup = xray_setup
