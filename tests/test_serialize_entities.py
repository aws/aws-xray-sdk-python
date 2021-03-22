import ast
import datetime
import json
import platform
import pytest

from aws_xray_sdk.version import VERSION
from aws_xray_sdk.core.models import http
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment
    
from .util import entity_to_dict
	
def test_serialize_segment():

    segment = Segment('test')
    segment.close()
        
    expected_segment_dict = {
    "name": "test",
    "start_time": segment.start_time,
    "trace_id": segment.trace_id,
    "end_time": segment.end_time,
    "in_progress": False,
    "id": segment.id
    }
    
    actual_segment_dict = entity_to_dict(segment)
    
    assert expected_segment_dict == actual_segment_dict
    
def test_serialize_segment_with_aws():

    segment = Segment('test')
    
    XRAY_META = {
        'xray': {
            'sdk': 'X-Ray for Python',
            'sdk_version': VERSION
        }
    }
    
    segment.set_aws(XRAY_META)
    
    segment.close()
    
    expected_segment_dict = {
    "name": "test",
    "start_time": segment.start_time,
    "trace_id": segment.trace_id,
    "end_time": segment.end_time,
    "in_progress": False,
    "aws": {
        "xray": {
            "sdk": "X-Ray for Python",
            "sdk_version": VERSION
        }
    },
    "id": segment.id
    }
    
    actual_segment_dict = entity_to_dict(segment)
    
    assert  expected_segment_dict == actual_segment_dict
    
def test_serialize_segment_with_services():

    segment = Segment('test')
    
    SERVICE_INFO = {
        'runtime': platform.python_implementation(),
        'runtime_version': platform.python_version()
    }
    
    segment.set_service(SERVICE_INFO)
    
    segment.close()
    
    expected_segment_dict = {
    "name": "test",
    "start_time": segment.start_time,
    "trace_id": segment.trace_id,
    "end_time": segment.end_time,
    "in_progress": False,
    "service": {
        "runtime": segment.service['runtime'],
        "runtime_version": segment.service['runtime_version']
    },
    "id": segment.id
    }
    
    actual_segment_dict = entity_to_dict(segment)
    
    assert  expected_segment_dict == actual_segment_dict 
    
def test_serialize_segment_with_annotation():

    segment = Segment('test')
    
    segment.put_annotation('key', 'value')
    
    segment.close()
    
    expected_segment_dict = {
    "id": segment.id,
    "name": "test",
    "start_time": segment.start_time,
    "in_progress": False,
    "annotations": {
        "key": "value"
    },
    "trace_id": segment.trace_id,
    "end_time": segment.end_time
    }
 
    actual_segment_dict = entity_to_dict(segment)
      
    assert  expected_segment_dict == actual_segment_dict
    
def test_serialize_segment_with_metadata():

    class TestMetadata():
        def __init__(self, parameter_one, parameter_two):
            self.parameter_one = parameter_one
            self.parameter_two = parameter_two
        
            self.parameter_three = {'test'} #set
            self.parameter_four = {'a': [1, 2, 3], 'b': True, 'c': (1.1, 2.2), 'd': list} #dict
            self.parameter_five = [TestSubMetadata(datetime.time(9, 25, 31)), TestSubMetadata(datetime.time(23, 14, 6))] #list
        
    class TestSubMetadata():
        def __init__(self, time):
            self.time = time

    segment = Segment('test')
    
    segment.put_metadata('key_one', TestMetadata(1,2), 'namespace_one')
    segment.put_metadata('key_two', TestMetadata(3,4), 'namespace_two')
    
    segment.close()
    
    expected_segment_dict = {
    "id": segment.id,
    "name": "test",
    "start_time": segment.start_time,
    "in_progress": False,
    "metadata": {
        "namespace_one": {
            "key_one": {
                "parameter_one": 1,
                "parameter_two": 2,
                "parameter_three": [
                    "test"
                ],
                "parameter_four": {
                    "a": [
                        1,
                        2,
                        3
                    ],
                    "b": True,
                    "c": [
                        1.1,
                        2.2
                    ],
                    "d": str(list)
                },
                "parameter_five": [
                    {
                        "time": "09:25:31"
                    },
                    {
                        "time": "23:14:06"
                    }
                ]
            }
        },
        "namespace_two": {
            "key_two": {
                "parameter_one": 3,
                "parameter_two": 4,
                "parameter_three": [
                    "test"
                ],
                "parameter_four": {
                    "a": [
                        1,
                        2,
                        3
                    ],
                    "b": True,
                    "c": [
                        1.1,
                        2.2
                    ],
                    "d": str(list)
                },
                "parameter_five": [
                    {
                        "time": "09:25:31"
                    },
                    {
                        "time": "23:14:06"
                    }
                ]
            }
        }
    },
    "trace_id": segment.trace_id,
    "end_time": segment.end_time
    }

    actual_segment_dict = entity_to_dict(segment) 
    
    assert  expected_segment_dict == actual_segment_dict
    
def test_serialize_segment_with_http():

    segment = Segment('test')
    
    segment.put_http_meta(http.URL, 'https://aws.amazon.com')
    segment.put_http_meta(http.METHOD, 'get')
    segment.put_http_meta(http.USER_AGENT, 'test')
    segment.put_http_meta(http.CLIENT_IP, '127.0.0.1')
    segment.put_http_meta(http.X_FORWARDED_FOR, True)
    segment.put_http_meta(http.STATUS, 200)
    segment.put_http_meta(http.CONTENT_LENGTH, 0)
    
    segment.close()
    
    expected_segment_dict = {
    "id": segment.id,
    "name": "test",
    "start_time": segment.start_time,
    "in_progress": False,
    "http": {
        "request": {
            "url": "https://aws.amazon.com",
            "method": "get",
            "user_agent": "test",
            "client_ip": "127.0.0.1",
            "x_forwarded_for": True
        },
        "response": {
            "status": 200,
            "content_length": 0
        }
    },
    "trace_id": segment.trace_id,
    "end_time": segment.end_time
    }

    actual_segment_dict = entity_to_dict(segment)
    
    assert expected_segment_dict == actual_segment_dict
    
def test_serialize_segment_with_exception():

    class TestException(Exception):
        def __init__(self, message):
            super(TestException, self).__init__(message)

    segment = Segment('test')
    
    stack_one = [
        ('/path/to/test.py', 10, 'module', 'another_function()'),
        ('/path/to/test.py', 3, 'another_function', 'wrong syntax')
    ]
    
    stack_two = [
        ('/path/to/test.py', 11, 'module', 'another_function()'),
        ('/path/to/test.py', 4, 'another_function', 'wrong syntax')
    ]

    exception_one = TestException('test message one')
    exception_two = TestException('test message two')

    segment.add_exception(exception_one, stack_one, True)
    segment.add_exception(exception_two, stack_two, False)
    
    segment.close()
    
    expected_segment_dict = {
    "id": segment.id,
    "name": "test",
    "start_time": segment.start_time,
    "in_progress": False,
    "cause": {
        "working_directory": segment.cause['working_directory'],
        "exceptions": [
            {
                "id": exception_one._cause_id,
                "message": "test message one",
                "type": "TestException",
                "remote": True,
                "stack": [
                    {
                        "path": "test.py",
                        "line": 10,
                        "label": "module"
                    },
                    {
                        "path": "test.py",
                        "line": 3,
                        "label": "another_function"
                    }
                ]
            },
            {
                "id": exception_two._cause_id,
                "message": "test message two",
                "type": "TestException",
                "remote": False,
                "stack": [
                    {
                        "path": "test.py",
                        "line": 11,
                        "label": "module"
                    },
                    {
                        "path": "test.py",
                        "line": 4,
                        "label": "another_function"
                    }
                ]
            }
        ]
    },
    "trace_id": segment.trace_id,
    "fault": True,
    "end_time": segment.end_time
    }

    actual_segment_dict = entity_to_dict(segment) 
    
    assert expected_segment_dict == actual_segment_dict
    
def test_serialize_subsegment():

    segment = Segment('test')
    subsegment = Subsegment('test', 'local', segment)
    
    subsegment.close()  
    segment.close()

    expected_subsegment_dict = {
    "id": subsegment.id,
    "name": "test",
    "start_time": subsegment.start_time,
    "in_progress": False,
    "trace_id": subsegment.trace_id,
    "type": "subsegment",
    "namespace": "local",
    "end_time": subsegment.end_time
    }

    actual_subsegment_dict = entity_to_dict(subsegment)
    
    assert expected_subsegment_dict == actual_subsegment_dict
    
def test_serialize_subsegment_with_http():

    segment = Segment('test')
    subsegment = Subsegment('test', 'remote', segment)
    
    subsegment.put_http_meta(http.URL, 'https://aws.amazon.com')
    subsegment.put_http_meta(http.METHOD, 'get')

    subsegment.put_http_meta(http.STATUS, 200)
    subsegment.put_http_meta(http.CONTENT_LENGTH, 0)
    
    subsegment.close()  
    segment.close()

    expected_subsegment_dict = {
    "id": subsegment.id,
    "name": "test",
    "start_time": subsegment.start_time,
    "in_progress": False,
    "http": {
        "request": {
            "url": "https://aws.amazon.com",
            "method": "get"
        },
        "response": {
            "status": 200,
            "content_length": 0
        }
    },
    "trace_id": subsegment.trace_id,
    "type": "subsegment",
    "namespace": "remote",
    "end_time": subsegment.end_time
    }

    actual_subsegment_dict = entity_to_dict(subsegment)
    
    assert expected_subsegment_dict == actual_subsegment_dict
     
def test_serialize_subsegment_with_sql():

    segment = Segment('test')
    subsegment = Subsegment('test', 'remote', segment)
    
    sql = {
        "url": "jdbc:postgresql://aawijb5u25wdoy.cpamxznpdoq8.us-west-2.rds.amazonaws.com:5432/ebdb",
        "preparation": "statement",
        "database_type": "PostgreSQL",
        "database_version": "9.5.4",
        "driver_version": "PostgreSQL 9.4.1211.jre7",
        "user" : "dbuser",
        "sanitized_query" : "SELECT  *  FROM  customers  WHERE  customer_id=?;"
    }

    subsegment.set_sql(sql)
    
    subsegment.close()  
    segment.close()

    expected_subsegment_dict = {
    "id": subsegment.id,
    "name": "test",
    "start_time": subsegment.start_time,
    "in_progress": False,
    "trace_id": subsegment.trace_id,
    "type": "subsegment",
    "namespace": "remote",
    "sql": {
        "url": "jdbc:postgresql://aawijb5u25wdoy.cpamxznpdoq8.us-west-2.rds.amazonaws.com:5432/ebdb",
        "preparation": "statement",
        "database_type": "PostgreSQL",
        "database_version": "9.5.4",
        "driver_version": "PostgreSQL 9.4.1211.jre7",
        "user": "dbuser",
        "sanitized_query": "SELECT  *  FROM  customers  WHERE  customer_id=?;"
    },
    "end_time": subsegment.end_time
    }

    actual_subsegment_dict = entity_to_dict(subsegment)
    
    assert expected_subsegment_dict == actual_subsegment_dict
    
def test_serialize_subsegment_with_aws():

    segment = Segment('test')
    subsegment = Subsegment('test', 'aws', segment)
    
    aws = {
        "bucket_name": "testbucket",
        "region": "us-east-1",
        "operation": "GetObject",
        "request_id": "0000000000000000",
        "key": "123",
        "resource_names": [
            "testbucket"
        ]
    }
    
    subsegment.set_aws(aws)
    
    subsegment.close()
    segment.close()
    
    expected_subsegment_dict = {
    "id": subsegment.id,
    "name": "test",
    "start_time": subsegment.start_time,
    "in_progress": False,
    "aws": {
        "bucket_name": "testbucket",
        "region": "us-east-1",
        "operation": "GetObject",
        "request_id": "0000000000000000",
        "key": "123",
        "resource_names": [
            "testbucket"
        ]
    },
    "trace_id": subsegment.trace_id,
    "type": "subsegment",
    "namespace": "aws",
    "end_time": subsegment.end_time
    }

    actual_subsegment_dict = entity_to_dict(subsegment)
    
    assert expected_subsegment_dict == actual_subsegment_dict
    
def test_serialize_with_ast_metadata():

    class_string = """\
class A:
    def __init__(self, a):
        self.a = a
"""
    
    ast_obj = ast.parse(class_string)
    
    segment = Segment('test')
    
    segment.put_metadata('ast', ast_obj)
    
    segment.close()

    actual_segment_dict = entity_to_dict(segment)
        
    assert  'ast' in actual_segment_dict['metadata']['default']
