from setuptools import setup, find_packages
from os import path
from aws_xray_sdk.version import VERSION

CURRENT_DIR = path.abspath(path.dirname(__file__))

with open(path.join(CURRENT_DIR, 'README.md'), 'r') as f:
    long_description = f.read()

setup(
    name='aws-xray-sdk',
    version=VERSION,

    description='The AWS X-Ray SDK for Python (the SDK) enables Python developers to record'
                ' and emit information from within their applications to the AWS X-Ray service.',
    long_description=long_description,
    long_description_content_type='text/markdown',

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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    install_requires=[
        'enum34;python_version<"3.4"',
        'wrapt',
        'future;python_version<"3"',
        'botocore>=1.11.3',
    ],

    keywords='aws xray sdk',

    packages=find_packages(exclude=['tests*']),
    include_package_data=True
)
