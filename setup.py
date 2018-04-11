from setuptools import setup, find_packages
from os import path
from aws_xray_sdk.version import VERSION

CURRENT_DIR = path.abspath(path.dirname(__file__))

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    read_md = lambda f: open(f, 'r').read()

long_description = read_md(path.join(CURRENT_DIR, 'README.md'))

setup(
    name='aws-xray-sdk',
    version=VERSION,

    description='The AWS X-Ray SDK for Python (the SDK) enables Python developers to record'
                ' and emit information from within their applications to the AWS X-Ray service.',
    long_description=long_description,

    url='https://github.com/aws/aws-xray-sdk-python',

    author='Amazon Web Services',

    license="Apache License 2.0",

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    install_requires=['jsonpickle', 'wrapt', 'requests', 'future'],

    keywords='aws xray sdk',

    packages=find_packages(exclude=['tests*']),
    include_package_data=True
)
