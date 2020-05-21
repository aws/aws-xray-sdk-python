import logging
from future.standard_library import install_aliases
from urllib.request import urlopen, Request

install_aliases()

log = logging.getLogger(__name__)

SERVICE_NAME = 'ec2'
ORIGIN = 'AWS::EC2::Instance'
IMDS_URL = 'http://169.254.169.254/latest/'


def initialize():
    """
    Try to get EC2 instance-id and AZ if running on EC2
    by querying http://169.254.169.254/latest/meta-data/.
    If not continue.
    """
    global runtime_context

    # Try the IMDSv2 endpoint for metadata
    try:
        runtime_context = {}

        # get session token with 60 seconds TTL to not have the token lying around for a long time
        token = do_request(url=IMDS_URL + "api/token",
                           headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
                           method="PUT")

        # get instance-id metadata
        runtime_context['instance_id'] = do_request(url=IMDS_URL + "meta-data/instance-id",
                                                    headers={"X-aws-ec2-metadata-token": token},
                                                    method="GET")

        # get availability-zone metadata
        runtime_context['availability_zone'] = do_request(url=IMDS_URL + "meta-data/placement/availability-zone",
                                                          headers={"X-aws-ec2-metadata-token": token},
                                                          method="GET")

    except Exception as e:
        # Falling back to IMDSv1 endpoint
        log.debug("failed to get ec2 instance metadata from IMDSv2 due to {}. Falling back to IMDSv1".format(e))

        try:
            runtime_context = {}

            runtime_context['instance_id'] = do_request(url=IMDS_URL + "meta-data/instance-id")

            runtime_context['availability_zone'] = do_request(url=IMDS_URL + "meta-data/placement/availability-zone-1")

        except Exception as e:
            runtime_context = None
            log.debug("failed to get ec2 instance metadata from IMDSv1 due to {}".format(e))
            log.warning("Failed to get ec2 instance metadata")


def do_request(url, headers=None, method="GET"):
    if headers is None:
        headers = {}

    if url is None:
        return None
        
    req = Request(url=url)
    req.headers = headers
    req.method = method
    res = urlopen(req, timeout=1)
    return res.read().decode('utf-8')
