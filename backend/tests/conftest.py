"""Fixtures that are used in the tests.

The fixtures are used to create the test environment and to provide the test data.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"


import datetime
import json
import os
import sys
import uuid
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

# Add the backend directory to the sys path
backend_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, backend_dir)

# Add the lambda directory to the sys path
lambda_dir = os.path.join(backend_dir, "lambda")
sys.path.insert(0, lambda_dir)


@pytest.fixture
def aws_event() -> dict:
    """A fixture that provides an AWS event.

    This fixture is used to provide an AWS event to the test functions.

    Returns:
        dict: The AWS event.
    """
    return {
        "body": json.dumps(
            {
                "message": "Hello, world!",
                "resource": "/test",
                "path": "/test",
                "httpMethod": "POST",
                "headers": {"Content-Type": "application/json", "Accept": "*/*", "User-Agent": "MartyChat/1.0 Test"},
                "requestContext": {"identity": {"sourceIp": "127.0.0.1"}},
            }
        )
    }


@pytest.fixture
def lambda_context() -> MagicMock:
    """A fixture that provides a Lambda context.

    This fixture is used to provide a Lambda context to the test functions.

    Returns:
        MagicMock: The Lambda context.
    """
    context = MagicMock()

    current_date = datetime.datetime.now().strftime("%Y/%m/%d")

    aws_region = os.getenv("REGION_NAME", "us-east-1")
    aws_account_id = os.getenv("AWS_ACCOUNT_ID", "123456789012")

    # Set the context attributes.
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    context.invoked_function_arn = f"arn:aws:lambda:{aws_region}:{aws_account_id}:function:test-function"
    context.memory_limit_in_mb = 128
    context.aws_request_id = str(uuid.uuid4())
    context.log_group_name = "/aws/lambda/test-function"
    context.log_stream_name = f"${current_date}/[$LATEST]{uuid.uuid4().hex}"
    context.get_remaining_time_in_millis.return_value = 3000

    return context


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """A fixture that mocks the environment variables.

    This fixture is used to mock the environment variables for the test functions.
    """
    # TODO: Hide secrets in the environment variables.
    with patch.dict(
        os.environ,
        {
            "ENV": "development",
            "REGION_NAME": "us-east-1",
            "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000",
            "NEXT_PUBLIC_API_URL": "http://localhost:8000",
            "NEXT_PUBLIC_LAMBDA_URL": "http://localhost:9000",
            "API_SECRETS_PARAM": "/martychat/secrets/api_keys",
            "PINECONE_ENV_PARAM": "/marty/pinecone/env",
            "PINECONE_INDEX_PARAM": "/marty/pinecone/index",
            "COGNITO_USER_PARAM": "/martychat/dev/cognito_user_pool_id",
            "COGNITO_CLIENT_PARAM": "/martychat/dev/cognito_app_client_id",
            "INFRA_SECRETS_PARAM": "/martychat/secrets/infrastructure_keys_dev",
        },
    ):
        yield


@pytest.fixture
def mock_boto3_session() -> Generator[tuple[MagicMock, MagicMock], None, None]:
    """A fixture that mocks the Boto3 session.

    This fixture is used to mock the Boto3 session for the test functions.
    """
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    with patch("boto3.session.Session", return_value=mock_session):
        yield mock_session, mock_client


@pytest.fixture
def mock_ssm_parameter(mock_boto3_session: MagicMock) -> MagicMock:
    """A fixture that mocks the SSM parameter.

    This fixture is used to mock the SSM parameter for the test functions.

    Args:
        mock_boto3_session (MagicMock): The mocked Boto3 session.

    Returns:
        MagicMock: The mocked SSM parameter.
    """
    _, mock_client = mock_boto3_session
    mock_client.get_parameter.return_value = {"Parameter": {"Value": "test-value"}}
    return mock_client
