# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
from flask import Flask
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy
import requests
import os

application = app = Flask(__name__)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

xray_recorder.configure(service='My Flask Web Application')
XRayMiddleware(app, xray_recorder)
patch_all()

db = XRayFlaskSqlAlchemy(app=application)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)


# test http instrumentation
@app.route('/outgoing-http-call')
def callHTTP():
    requests.get("https://aws.amazon.com")
    return "Ok! tracing outgoing http call"


# test aws sdk instrumentation
@app.route('/aws-sdk-call')
def callAWSSDK():
    client = boto3.client('s3')
    client.list_buckets()

    return 'Ok! tracing aws sdk call'


# test flask-sql alchemy instrumentation
@app.route('/flask-sql-alchemy-call')
def callSQL():
    name = 'sql-alchemy-model'
    user = User(name=name)
    db.create_all()
    db.session.add(user)

    return 'Ok! tracing sql call'


@app.route('/')
def default():
    return "healthcheck"


if __name__ == "__main__":
    address = os.environ.get('LISTEN_ADDRESS')

    if address is None:
        host = '127.0.0.1'
        port = '5000'
    else:
        host, port = address.split(":")
    app.run(host=host, port=int(port), debug=True)
