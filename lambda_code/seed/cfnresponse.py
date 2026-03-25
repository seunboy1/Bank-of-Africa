"""
CloudFormation Custom Resource response helper.
Standard implementation — sends success/failure signals back to CloudFormation.
"""

import json
import urllib.request


SUCCESS = "SUCCESS"
FAILED = "FAILED"


def send(event, context, response_status, response_data, physical_resource_id=None, no_echo=False, reason=None):
    response_url = event["ResponseURL"]

    response_body = {
        "Status": response_status,
        "Reason": reason or f"See CloudWatch Log Stream: {context.log_stream_name}",
        "PhysicalResourceId": physical_resource_id or context.log_stream_name,
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "NoEcho": no_echo,
        "Data": response_data,
    }

    json_body = json.dumps(response_body).encode("utf-8")
    req = urllib.request.Request(response_url, data=json_body, headers={"Content-Type": "", "Content-Length": str(len(json_body))}, method="PUT")

    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Failed to send CFN response: {e}")
