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
import logging
import os
import sys
import time
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


@pytest.hookimpl(tryfirst=True)
def pytest_configure() -> None:
    """Configure the pytest logging.

    This function configures the pytest logging to display the logging messages in the console.
    """
    log_dir = "backend/tests/logs"
    os.makedirs(log_dir, exist_ok=True)  # Ensure log directory exists

    file_timestamp = time.strftime("%Y%m%d%H%M%S")
    log_file = os.path.join(log_dir, f"pytest-{file_timestamp}.log")

    log_timestamp_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,  # Set log level to capture all messages
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt=log_timestamp_format,
    )

    log_timestamp = time.strftime(log_timestamp_format)
    logging.info("========== Pytest Session Started ==========")
    logging.info("Test session started at: %s", log_timestamp)
    logging.info(f"Logging to: {log_file}")


@pytest.hookimpl(trylast=True)
def pytest_unconfigure() -> None:
    """Finish the pytest logging when the test session ends.

    This function completes the pytest logging to display the logging messages in the console when the test session
    ends.
    """
    log_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    logging.info("Test session ended at: %s", log_timestamp)
    logging.info("========== Pytest Session Ended ==========")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logstart(nodeid: str, location: str) -> None:
    """Format the log message at the start of the test.

    This function formats the log message at the start of the test.

    Args:
        nodeid (str): The node ID of the test.
        location (str): The location of the test.
    """
    logging.info("=" * 93)
    logging.info(f"STARTING TEST: {nodeid}")
    logging.info("=" * 93)


@pytest.hookimpl(trylast=True)
def pytest_runtest_logfinish(nodeid: str, location: str) -> None:
    """Format the log message at the end of the test.

    This function formats the log message at the end of the test.

    Args:
        nodeid (str): The node ID of the test.
        location (str): The location of the test.
    """
    logging.info("=" * 93)
    logging.info(f"FINISHED TEST: {nodeid}")
    logging.info("=" * 93 + "\n")


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
            "API_SECRETS_PARAM": "/path/to/api_secrets",
            "PINECONE_ENV_PARAM": "/path/to/pinecone_env",
            "PINECONE_INDEX_PARAM": "/path/to/pinecone_index",
            "COGNITO_USER_PARAM": "/path/to/cognito_user_pool_id",
            "COGNITO_CLIENT_PARAM": "/path/to/cognito_client_id",
            "DYNAMODB_USER_TABLE_PARAM": "/path/to/dynamodb/user/table",
            "INFRA_SECRETS_PARAM": "/path/to/infra_secrets",
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
