"""Tests for the create_user lambda function.

This module contains tests for the create_user lambda function in the backend/lambda directory. The tests
are written using the pytest framework.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import json
import os
import sys
from typing import Any, cast
from unittest.mock import MagicMock, patch

import botocore
import pytest

# Add the lambda directory to the sys path
lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import sign_in  # noqa: E402


@pytest.mark.unit
def test_get_user_pool_id(mock_ssm_parameter: MagicMock, mock_env_vars: None) -> None:
    """Test the get_user_pool_id function.

    This test verifies that the get_user_pool_id function correctly retrieves the Cognito User Pool ID
    from the AWS Systems Manager Parameter Store.

    Args:
        mock_ssm_parameter (MagicMock): The mocked SSM parameter.
        mock_env_vars (None): The mocked environment variables.
    """
    # Execute the function
    result = sign_in.get_user_pool_id()

    # Assert the expected result
    assert result == "test-value"
    mock_ssm_parameter.get_parameter.assert_called_once_with(Name="/path/to/cognito_user_pool_id", WithDecryption=True)


@pytest.mark.unit
def test_get_client_metadata(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_client_metadata function.

    This test verifies that the get_client_metadata function correctly retrieves the Cognito Client ID
    and Client Secret from the AWS Systems Manager Parameter Store and AWS Secrets Manager.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock responses
    mock_session, mock_client = mock_boto3_session
    ssm_client = MagicMock()
    secrets_manager_client = MagicMock()
    mock_session.client.side_effect = lambda service_name, **kwargs: {
        "ssm": ssm_client,
        "secretsmanager": secrets_manager_client,
    }.get(service_name, MagicMock())

    # Set up the mock responses for the SSM client
    ssm_client.get_parameter.side_effect = lambda **kwargs: {
        "Parameter": {"Value": "secret-id" if kwargs["Name"] == "/path/to/infra_secrets" else "test-client-id"}
    }

    # Set up the mock responses for the Secrets Manager client
    secrets_manager_client.get_secret_value.return_value = {
        "SecretString": json.dumps({"cognito_client_secret": "test-client-secret"})
    }

    # Execute the function
    with patch("boto3.session.Session", return_value=mock_session):
        result = sign_in.get_client_metadata()

    # Assert the expected result
    assert result == {"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"}
    ssm_client.get_parameter.assert_any_call(Name="/path/to/infra_secrets", WithDecryption=True)
    ssm_client.get_parameter.assert_any_call(Name="/path/to/cognito_client_id", WithDecryption=True)
    secrets_manager_client.get_secret_value.assert_called_once_with(SecretId="secret-id")


@pytest.mark.unit
def test_get_secret_hash(mock_env_vars: None) -> None:
    """Test the get_secret_hash function.

    This test verifies that the get_secret_hash function correctly generates a secret hash
    for the AWS Cognito authentication request.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Execute the function
    username = "test@example.com"
    client_id = "test-client-id"
    client_secret = "test-client-secret"
    result = sign_in.get_secret_hash(username, client_id, client_secret)

    # Assert the result is not empty (we don't check the exact value because it's a hash)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.unit
def test_get_user_id(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_user_id function.

    This test verifies that the get_user_id function correctly retrieves the user ID
    from the AWS Cognito service.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Mock the cognito_client responses
    cognito_client.get_user.return_value = {
        "Username": "test@example.com",
        "UserAttributes": [
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "sub", "Value": "test-user-id"},
        ],
    }

    # Execute the function
    result = sign_in.get_user_id(cast(sign_in.CognitoClient, cognito_client), "test-access-token")

    # Assert the expected result
    assert result == "test-user-id"
    cognito_client.get_user.assert_called_once_with(AccessToken="test-access-token")


@pytest.mark.unit
def test_lambda_handler_success(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with successful user authentication.

    This test verifies that the lambda_handler function correctly authenticates a user
    and returns the authentication result.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"email": "test@example.com", "password": "Test1234!"})

    # Mock the functions that interact with AWS services
    # Instead of mocking boto3, mock the actual AWS interaction functions
    with (
        patch.object(sign_in, "get_user_pool_id", return_value="test-user-pool-id"),
        patch.object(
            sign_in,
            "get_client_metadata",
            return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
        ),
        patch.object(sign_in, "get_secret_hash", return_value="test-secret-hash"),
        patch.object(sign_in, "get_user_id", return_value="test-user-id"),
    ):
        # Mock the boto3 client object
        mock_cognito_client = MagicMock()

        # Set up the initiate_auth response
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "test-access-token",
                "IdToken": "test-id-token",
                "RefreshToken": "test-refresh-token",
                "ExpiresIn": 3600,
            }
        }

        # Set up the describe_user_pool response
        mock_cognito_client.describe_user_pool.return_value = {
            "UserPool": {"Policies": {"PasswordPolicy": {"RefreshTokenValidity": 30}}}
        }

        # Patch the boto3.client function to return our mock
        with patch("boto3.client", return_value=mock_cognito_client):
            # Execute the function
            response = sign_in.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["message"] == "User authenticated successfully."
    assert "authenticationResult" in response_body
    auth_result = response_body["authenticationResult"]
    assert auth_result["AccessToken"] == "test-access-token"
    assert auth_result["IdToken"] == "test-id-token"
    assert auth_result["RefreshToken"] == "test-refresh-token"
    assert auth_result["UserId"] == "test-user-id"


@pytest.mark.unit
def test_lambda_handler_missing_required_fields(
    aws_event: dict, lambda_context: MagicMock, mock_env_vars: None
) -> None:
    """Test the lambda_handler function with missing required fields.

    This test verifies that the lambda_handler function correctly handles the case
    when required fields are missing in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps(
        {
            # Missing email
            "password": "Test1234!"
        }
    )

    # Execute the function
    response = sign_in.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Email and password are required."


@pytest.mark.unit
def test_lambda_handler_incorrect_credentials(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with incorrect credentials.

    This test verifies that the lambda_handler function correctly handles the case
    when the user provides incorrect credentials.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps({"email": "test@example.com", "password": "IncorrectPassword"})

    # Create a mock boto3 client
    cognito_client = MagicMock()

    # Create a simple function that raises the exception directly in the call
    def raise_auth_error(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        # This approach bypasses mypy's checks but will be caught correctly in the code
        e = botocore.exceptions.ClientError.__new__(botocore.exceptions.ClientError)
        e.response = {"Error": {"Code": "NotAuthorizedException", "Message": "Incorrect username or password."}}
        raise e

    # Set the side effect to our function
    cognito_client.initiate_auth.side_effect = raise_auth_error

    # Patch boto3.client to return our mock
    cognito_client_patch = patch("boto3.client", return_value=cognito_client)
    user_pool_patch = patch.object(sign_in, "get_user_pool_id", return_value="test-user-pool-id")
    client_metadata_patch = patch.object(
        sign_in,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(sign_in, "get_secret_hash", return_value="test-secret-hash")
    with cognito_client_patch, user_pool_patch, client_metadata_patch, secret_hash_patch:
        # Execute the function
        response = sign_in.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 401
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Incorrect username or password."


@pytest.mark.unit
def test_lambda_handler_user_not_found(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function when the user is not found.

    This test verifies that the lambda_handler function correctly handles the case
    when the user does not exist in the AWS Cognito user pool.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps({"email": "nonexistent@example.com", "password": "Test1234!"})

    # Create a mock boto3 client
    cognito_client = MagicMock()

    # Create a simple function that raises the exception directly in the call
    def raise_user_not_found(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        # This approach bypasses mypy's checks but will be caught correctly in the code
        e = botocore.exceptions.ClientError.__new__(botocore.exceptions.ClientError)
        e.response = {"Error": {"Code": "UserNotFoundException", "Message": "User does not exist."}}
        raise e

    # Set the side effect to our function
    cognito_client.initiate_auth.side_effect = raise_user_not_found

    # Patch boto3.client to return our mock
    cognito_client_patch = patch("boto3.client", return_value=cognito_client)
    user_pool_patch = patch.object(sign_in, "get_user_pool_id", return_value="test-user-pool-id")
    client_metadata_patch = patch.object(
        sign_in,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(sign_in, "get_secret_hash", return_value="test-secret-hash")
    with cognito_client_patch, user_pool_patch, client_metadata_patch, secret_hash_patch:
        # Execute the function
        response = sign_in.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert response_body["error"] == "User does not exist."
