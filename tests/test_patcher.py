import inspect
import pytest
import sys
import wrapt
try:
    # Python versions >= 3.4
    from importlib import reload
except ImportError:
    # Python versions 3 <= x < 3.4 have reload in the imp module
    try:
        from imp import reload
    except ImportError:
        # Python versions < 3 have reload built-in
        pass

from aws_xray_sdk.core import patcher, xray_recorder
from aws_xray_sdk.core.context import Context


TEST_MODULES = (
    'tests.mock_module',
    'tests.mock_module.mock_file',
    'tests.mock_module.mock_submodule',
    'tests.mock_module.mock_submodule.mock_subfile',
)


@pytest.fixture(autouse=True)
def construct_ctx():
    """
    Clean up context storage on each test run and begin a segment
    so that later subsegment can be attached. After each test run
    it cleans up context storage again.
    """
    pre_run_modules = set(module for module in sys.modules.keys())

    xray_recorder.configure(service='test', sampling=False, context=Context())
    xray_recorder.clear_trace_entities()
    xray_recorder.begin_segment('name')
    yield
    xray_recorder.end_segment()
    xray_recorder.clear_trace_entities()

    # Reload wrapt.importer references to modules to start off clean
    reload(wrapt)
    reload(wrapt.importer)
    # Reload patcher references to already patched modules
    reload(patcher)
    # Cleanup the already imported module references in the system
    for module_name, module in sorted(sys.modules.items(), key=lambda m: len(m[0]), reverse=True):
        if module_name not in pre_run_modules and inspect.ismodule(module):
            reload(module)

    for module_name in sorted(sys.modules.keys(), key=lambda m: len(m), reverse=True):
        if module_name not in pre_run_modules:
            del sys.modules[module_name]


def _call_all_mock_functions():
    from .mock_module import mock_file, mock_init
    from .mock_module.mock_submodule import mock_subfile, mock_subinit

    mock_init()
    mock_subinit()
    mock_file.mock_func()
    mock_subfile.mock_subfunc()
    mock_subfile.mock_no_doublepatch()
    mock_subfile.MockClass.mock_classmethod()
    mock_subfile.MockClass.mock_staticmethod()
    mock_subfile.MockClass().mock_method()


@pytest.mark.parametrize('modules', [
    ('nonexisting.module',),
    ('psycopg2', 'nonexisting.module',),
    ('nonexisting.module', 'psycopg2',),
])
def test_incorrect_import_fails(modules):
    with pytest.raises(Exception) as e:
        patcher.patch(modules)
    assert str(e.value) == 'modules nonexisting.module are currently not supported for patching'


def test_external_file():
    patcher.patch(['tests.mock_module.mock_file'])
    assert len(xray_recorder.current_segment().subsegments) == 0
    # We want to make sure patching does not load any of the patched modules
    imported_modules = [module for module in TEST_MODULES if module in sys.modules]
    assert not imported_modules

    _call_all_mock_functions()

    assert len(xray_recorder.current_segment().subsegments) == 2
    assert xray_recorder.current_segment().subsegments[0].name == 'mock_func'
    assert xray_recorder.current_segment().subsegments[1].name == 'mock_no_doublepatch'  # It is patched with decorator


def test_external_module():
    patcher.patch(['tests.mock_module.mock_submodule'])
    assert len(xray_recorder.current_segment().subsegments) == 0
    # We want to make sure patching does not load any of the patched modules
    imported_modules = [module for module in TEST_MODULES if module in sys.modules]
    assert not imported_modules

    _call_all_mock_functions()

    assert len(xray_recorder.current_segment().subsegments) == 7
    assert xray_recorder.current_segment().subsegments[0].name == 'mock_subinit'
    assert xray_recorder.current_segment().subsegments[1].name == 'mock_subfunc'
    assert xray_recorder.current_segment().subsegments[2].name == 'mock_no_doublepatch'  # Should appear only once
    assert xray_recorder.current_segment().subsegments[3].name == 'mock_classmethod'
    assert xray_recorder.current_segment().subsegments[4].name == 'mock_staticmethod'
    assert xray_recorder.current_segment().subsegments[5].name == 'MockClass.__init__'
    assert xray_recorder.current_segment().subsegments[6].name == 'mock_method'


def test_external_submodules_full():
    patcher.patch(['tests.mock_module'])
    assert len(xray_recorder.current_segment().subsegments) == 0
    # We want to make sure patching does not load any of the patched modules
    imported_modules = [module for module in TEST_MODULES if module in sys.modules]
    assert not imported_modules

    _call_all_mock_functions()

    assert len(xray_recorder.current_segment().subsegments) == 9
    assert xray_recorder.current_segment().subsegments[0].name == 'mock_init'
    assert xray_recorder.current_segment().subsegments[1].name == 'mock_subinit'
    assert xray_recorder.current_segment().subsegments[2].name == 'mock_func'
    assert xray_recorder.current_segment().subsegments[3].name == 'mock_subfunc'
    assert xray_recorder.current_segment().subsegments[4].name == 'mock_no_doublepatch'
    assert xray_recorder.current_segment().subsegments[5].name == 'mock_classmethod'
    assert xray_recorder.current_segment().subsegments[6].name == 'mock_staticmethod'
    assert xray_recorder.current_segment().subsegments[7].name == 'MockClass.__init__'
    assert xray_recorder.current_segment().subsegments[8].name == 'mock_method'


def test_external_submodules_ignores_file():
    patcher.patch(['tests.mock_module'], ignore_module_patterns=['tests.mock_module.mock_file'])
    assert len(xray_recorder.current_segment().subsegments) == 0
    # We want to make sure patching does not load any of the patched modules
    imported_modules = [module for module in TEST_MODULES if module in sys.modules]
    assert not imported_modules

    _call_all_mock_functions()

    assert len(xray_recorder.current_segment().subsegments) == 8
    assert xray_recorder.current_segment().subsegments[0].name == 'mock_init'
    assert xray_recorder.current_segment().subsegments[1].name == 'mock_subinit'
    assert xray_recorder.current_segment().subsegments[2].name == 'mock_subfunc'
    assert xray_recorder.current_segment().subsegments[3].name == 'mock_no_doublepatch'
    assert xray_recorder.current_segment().subsegments[4].name == 'mock_classmethod'
    assert xray_recorder.current_segment().subsegments[5].name == 'mock_staticmethod'
    assert xray_recorder.current_segment().subsegments[6].name == 'MockClass.__init__'
    assert xray_recorder.current_segment().subsegments[7].name == 'mock_method'


def test_external_submodules_ignores_module():
    patcher.patch(['tests.mock_module'], ignore_module_patterns=['tests.mock_module.mock_submodule'])
    assert len(xray_recorder.current_segment().subsegments) == 0
    # We want to make sure patching does not load any of the patched modules
    imported_modules = [module for module in TEST_MODULES if module in sys.modules]
    assert not imported_modules

    _call_all_mock_functions()

    assert len(xray_recorder.current_segment().subsegments) == 3
    assert xray_recorder.current_segment().subsegments[0].name == 'mock_init'
    assert xray_recorder.current_segment().subsegments[1].name == 'mock_func'
    assert xray_recorder.current_segment().subsegments[2].name == 'mock_no_doublepatch'  # It is patched with decorator
