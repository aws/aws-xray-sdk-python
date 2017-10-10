import logging
import importlib

log = logging.getLogger(__name__)

SUPPORTED_MODULES = (
    'botocore',
    'requests',
    'sqlite3',
    'mysql',
)

_PATCHED_MODULES = set()


def patch_all():
    patch(SUPPORTED_MODULES, raise_errors=False)


def patch(modules_to_patch, raise_errors=True):
    for m in modules_to_patch:
        _patch_module(m, raise_errors)


def _patch_module(module_to_patch, raise_errors=True):
    # boto3 depends on botocore and patch botocore is sufficient
    if module_to_patch == 'boto3':
        module_to_patch = 'botocore'

    if module_to_patch not in SUPPORTED_MODULES:
        raise Exception('module %s is currently not supported for patching'
                        % module_to_patch)

    try:
        _patch(module_to_patch)
    except Exception:
        if raise_errors:
            raise
        log.debug('failed to patch module %s', module_to_patch)


def _patch(module_to_patch):

    path = 'aws_xray_sdk.ext.%s' % module_to_patch

    if module_to_patch in _PATCHED_MODULES:
        log.debug('%s already patched', module_to_patch)

    imported_module = importlib.import_module(path)
    imported_module.patch()

    _PATCHED_MODULES.add(module_to_patch)
    log.info('successfully patched module %s', module_to_patch)
