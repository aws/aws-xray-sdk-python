import ast
import importlib
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


def _xray_traced(wrapped, instance, args, kwargs):
    from aws_xray_sdk.core import xray_recorder

    with xray_recorder.capture(name=wrapped.__name__):
        return wrapped(*args, **kwargs)


class XRayPatcherVisitor(ast.NodeVisitor):
    def __init__(self, module):
        self.module = module
        self._current_classes = []
        self._patched_in_class = []

    def visit_FunctionDef(self, node):
        name = '.'.join(self._current_classes + [node.name])
        if self._patched_in_class:
            if name in self._patched_in_class[-1]:
                return
            self._patched_in_class[-1].add(name)
        try:
            wrapt.wrap_function_wrapper(
                self.module,
                name,
                _xray_traced
            )
        except Exception:
            log.warning('could not patch %s in %s', name, self.module)

    def visit_ClassDef(self, node):
        self._current_classes.append(node.name)
        self._patched_in_class.append(set())

        self.generic_visit(node)

        self._patched_in_class.pop()
        self._current_classes.pop()


def _patch_file(module, f):
    if module in _PATCHED_MODULES:
        log.debug('%s already patched', module)
        return

    with open(f) as open_file:
        tree = ast.parse(open_file.read())
    XRayPatcherVisitor(module).visit(tree)


def _on_file_import_factory(module, module_path):
    def on_import(hook):
        _patch_file(module, '{}.py'.format(module_path))
    return on_import


def _external_module_patch(module):
    if module.startswith('.'):
        raise Exception('relative packages not supported for patching: {}'.format(module))

    module_path = module.replace('.', '/')
    for loader, submodule_name, is_module in pkgutil.iter_modules([module_path]):
        submodule = '.'.join([module, submodule_name])
        if is_module:
            _external_module_patch(submodule)
        else:
            submodule_path = '/'.join([module_path, submodule_name])
            on_import = _on_file_import_factory(submodule, submodule_path)

            if submodule in sys.modules:
                on_import(None)
            else:
                wrapt.importer.when_imported(submodule)(on_import)

            _PATCHED_MODULES.add(submodule)
            log.info('successfully patched module %s', submodule)

    on_import = _on_file_import_factory(module, '{}/__init__'.format(module_path))
    if module in sys.modules:
        on_import(None)
    else:
        wrapt.importer.when_imported(module)(on_import)

    _PATCHED_MODULES.add(module)
    log.info('successfully patched module %s', module)
