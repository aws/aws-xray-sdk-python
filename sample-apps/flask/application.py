#!/usr/bin/env python

"""
flask application for demoing AWS X-Ray
https://aws.amazon.com/xray/
"""

import os
import requests
import boto3
import flask
import aws_xray_sdk.core as aws_core
import aws_xray_sdk.ext.flask.middleware as aws_flask_middleware
import aws_xray_sdk.ext.flask_sqlalchemy.query as aws_flask_sqlalchemy

application = app = flask.Flask(__name__)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

aws_core.xray_recorder.configure(
    service=os.getenv(
        'XRAY_SERVICE_NAME', 'My Flask Web Application'))

aws_flask_middleware.XRayMiddleware(
    app,
    aws_core.xray_recorder)

aws_core.patch_all()

db = (
    aws_flask_sqlalchemy.XRayFlaskSqlAlchemy(
        app=application))


class User(db.Model):
    """User."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


# test http instrumentation
@app.route('/outgoing-http-call')
def callHTTP():
    """callHTTP."""
    requests.get("https://aws.amazon.com")
    return "Ok! tracing outgoing http call"


# test aws sdk instrumentation
@app.route('/aws-sdk-call')
def callAWSSDK():
    """callAWSSDK."""
    client = boto3.client('s3')
    print(client.list_buckets())
    return 'Ok! tracing aws sdk call'


# test flask-sql alchemy instrumentation
@app.route('/flask-sql-alchemy-call')
def callSQL():
    """callSQL."""
    # add a custom subsegment with annotations
    # https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-python-subsegments.html
    # https://github.com/aws/aws-xray-sdk-python/blob/0e1f935bd2040ee7dbf0625db7f7ad780c66fb37/aws_xray_sdk/core/recorder.py#L341
    annotation_subsegment = aws_core.xray_recorder.begin_subsegment(
        'annotations')
    annotation_subsegment.put_annotation(
        'id', 12345)
    aws_core.xray_recorder.end_subsegment()
    # add a custom subsegment with metadata
    # https://docs.aws.amazon.com/xray/latest/devguide/xray-sdk-python-subsegments.html
    # https://github.com/aws/aws-xray-sdk-python/blob/0e1f935bd2040ee7dbf0625db7f7ad780c66fb37/aws_xray_sdk/core/recorder.py#L356
    metadata_subsegment = aws_core.xray_recorder.begin_subsegment(
        'metadata')
    metadata_subsegment.put_metadata(
        'custom-field-here', 'hello-world')
    aws_core.xray_recorder.end_subsegment()
    name = 'sql-alchemy-model'
    user = User(name=name)
    db.create_all()
    db.session.add(user)
    return 'Ok! tracing sql call'


@app.route('/')
def default():
    """default."""
    return "healthcheck"


if __name__ == "__main__":
    address = os.environ.get('LISTEN_ADDRESS')

    if address is None:
        host = '0.0.0.0'
        port = '5000'
    else:
        host, port = address.split(":")
    app.run(
        host=host,
        port=int(port),
        debug=True)
