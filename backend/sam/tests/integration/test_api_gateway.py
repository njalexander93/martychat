"""Module to test the API Gateway endpoint.

This module contains a test class to test the API Gateway endpoint. The test class uses the pytest framework to run the
tests. The test class contains a fixture to get the API Gateway URL from the Cloudformation stack outputs. The test
class contains a test method to call the API Gateway endpoint and check the response.
"""

import os

import boto3
import pytest
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test.
"""


class TestApiGateway:
    """Test class to test the API Gateway endpoint."""
    @pytest.fixture()
    def api_gateway_url(self) -> str:
        """Get the API Gateway URL from Cloudformation Stack outputs."""
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError("Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack")

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
            ) from e

        stacks = response["Stacks"]
        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "HelloWorldApi"]

        if not api_outputs:
            raise KeyError(f"HelloWorldAPI not found in stack {stack_name}")

        return api_outputs[0]["OutputValue"]  # Extract url from stack outputs

    def test_api_gateway(self, api_gateway_url: str) -> None:
        """Call the API Gateway endpoint and check the response."""
        response = requests.get(api_gateway_url)

        assert response.status_code == 200
        assert response.json() == {"message": "hello world"}
