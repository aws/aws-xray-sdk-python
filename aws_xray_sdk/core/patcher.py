import importlib
import inspect
import logging
import pkgutil
import sys
import wrapt

log = logging.getLogger(__name__)

SUPPORTED_MODULES = (
    'botocore',
    'pynamodb',
    'requests',
    'sqlite3',
    'mysql',
    'httplib',
    'pymongo',
    'psycopg2',
)

NO_DOUBLE_PATCH = (
    'botocore',
    'pynamodb',
    'requests',
    'sqlite3',
    'mysql',
    'pymongo',
    'psycopg2',
)

_PATCHED_MODULES = set()


def patch_all(double_patch=False):
    if double_patch:
        patch(SUPPORTED_MODULES, raise_errors=False)
    else:
        patch(NO_DOUBLE_PATCH, raise_errors=False)


def _is_valid_import(path):
    return bool(pkgutil.get_loader(path))


def patch(modules_to_patch, raise_errors=True):
    modules = set()
    for module_to_patch in modules_to_patch:
        # boto3 depends on botocore and patching botocore is sufficient
        if module_to_patch == 'boto3':
            modules.add('botocore')
        # aioboto3 depends on aiobotocore and patching aiobotocore is sufficient
        # elif module_to_patch == 'aioboto3':
        #     modules.add('aiobotocore')
        # pynamodb requires botocore to be patched as well
        elif module_to_patch == 'pynamodb':
            modules.add('botocore')
            modules.add(module_to_patch)
        else:
            modules.add(module_to_patch)

    unsupported_modules = modules - set(SUPPORTED_MODULES)
    native_modules = modules - unsupported_modules

    external_modules = set(module for module in unsupported_modules if _is_valid_import(module.replace('.', '/')))
    unsupported_modules = unsupported_modules - external_modules

    if unsupported_modules:
        raise Exception('modules %s are currently not supported for patching'
                        % ', '.join(unsupported_modules))

    for m in native_modules:
        _patch_module(m, raise_errors)

    for m in external_modules:
        _external_module_patch(m)


def _patch_module(module_to_patch, raise_errors=True):
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
        return

    imported_module = importlib.import_module(path)
    imported_module.patch()

    _PATCHED_MODULES.add(module_to_patch)
    log.info('successfully patched module %s', module_to_patch)


def _patch_func(parent, func_name, func):
    from aws_xray_sdk.core import xray_recorder

    setattr(parent, func_name, xray_recorder.capture()(func))


def _patch_class(module, cls):
    for member_name, member in inspect.getmembers(cls, inspect.isclass):
        if member.__module__ == module.__name__:
            _patch_class(module, member)

    for member_name, member in inspect.getmembers(cls, inspect.ismethod):
        if member.__module__ == module.__name__:
            _patch_func(cls, member_name, member)


def _on_import(module):
    for member_name, member in inspect.getmembers(module, inspect.isfunction):
        if member.__module__ == module.__name__:
            _patch_func(module, member_name, member)

    for member_name, member in inspect.getmembers(module, inspect.isclass):
        if member.__module__ == module.__name__:
            _patch_class(module, member)


def _external_module_patch(module):
    if module.startswith('.'):
        raise Exception('relative packages not supported for patching: {}'.format(module))

    for loader, submodule_name, is_module in pkgutil.iter_modules([module.replace('.', '/')]):
        submodule = '.'.join([module, submodule_name])
        if is_module:
            _external_module_patch(submodule)
        else:
            if submodule in sys.modules:
                _on_import(sys.modules[submodule])
            else:
                wrapt.importer.when_imported(submodule)(_on_import)

            _PATCHED_MODULES.add(submodule)
            log.info('successfully patched module %s', submodule)

    if module in sys.modules:
        _on_import(sys.modules[module])
    else:
        wrapt.importer.when_imported(module)(_on_import)

    _PATCHED_MODULES.add(module)
    log.info('successfully patched module %s', module)
