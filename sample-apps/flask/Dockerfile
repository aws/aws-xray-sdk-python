FROM python:3.9

ARG USER=driver
ARG UID=1000
ARG GID=1000

USER root
ENV HOME=/root

RUN echo "installing linux tools" \
    && apt-get update -y \
    && apt-get install -y less net-tools openssl \
    && echo "installing aws xray daemon https://docs.aws.amazon.com/xray/latest/devguide/xray-daemon.html" \
    && curl -s "https://s3.us-east-2.amazonaws.com/aws-xray-assets.us-east-2/xray-daemon/aws-xray-daemon-3.x.deb" -o aws-xray-daemon.deb \
    && dpkg -i aws-xray-daemon.deb \
    && rm -f aws-xray-daemon.deb \
    && echo "installing aws cli v2" \
    && curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip > /dev/null 2>&1 \
    && ./aws/install > /dev/null 2>&1 \
    && rm -f awscliv2.zip \
    && echo "adding custom user driver" \
    && groupadd -r driver -g ${GID} \
    && useradd -m --no-log-init -r -g driver -u ${UID} driver \
    && mkdir /opt/stack \
    && mkdir /opt/venv \
    && chown driver:driver /opt/stack /opt/venv

USER driver
ENV HOME=/home/driver

WORKDIR /opt/stack

ADD . /opt/stack

RUN echo "creating virtual env" \
    && python3.9 -m venv /opt/venv \
    && echo "---------------------------" \
    && echo "activating venv /opt/venv" \
    && . /opt/venv/bin/activate \
    && echo "---------------------------" \
    && echo "which python" \
    && which python \
    && echo "---------------------------" \
    && echo "upgrading pip and setuptools" \
    && pip install --upgrade pip setuptools \
    && echo "---------------------------" \
    && echo "upgrading pip and setuptools" \
    && pip install -r /opt/stack/requirements.txt \
    && echo "---------------------------" \
    && echo "which python" \
    && which python \
    && echo "---------------------------" \
    && echo "pip list" \
    && pip list

CMD ["python", "application.py"]
