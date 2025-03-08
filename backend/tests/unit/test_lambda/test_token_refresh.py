"""Tests for the token_refresh lambda function.

This module contains tests for the token_refresh lambda function in the backend/lambda directory. The tests
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
from unittest.mock import MagicMock, patch

import botocore
import pytest

# Add the lambda directory to the sys path
lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import token_refresh  # noqa: E402


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
    result = token_refresh.get_user_pool_id()

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
        result = token_refresh.get_client_metadata()

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
    result = token_refresh.get_secret_hash(username, client_id, client_secret)

    # Assert the result is not empty (we don't check the exact value because it's a hash)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.unit
def test_lambda_handler_success(
    aws_event: dict, lambda_context: MagicMock, mock_boto3_session: tuple, mock_env_vars: None
) -> None:
    """Test the lambda_handler function with successful user deletion.

    This test verifies that the lambda_handler function correctly deletes a user
    from both AWS Cognito and DynamoDB.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    aws_event["body"] = json.dumps({"refreshToken": "test-refresh-token", "userId": "test-user-id"})

    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Mock the cognito_client responses
    cognito_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "new-access-token",
            "IdToken": "new-id-token",
            "ExpiresIn": 3600,
        }
    }
    cognito_client.describe_user_pool.return_value = {
        "UserPool": {"Policies": {"PasswordPolicy": {"RefreshTokenValidity": 30}}}
    }

    # Mock the get_user_pool_id, get_client_metadata, and get_secret_hash functions
    user_pool_patch = patch.object(token_refresh, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_path = patch.object(
        token_refresh,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(token_refresh, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)

    # Execute the function and assert it raises the expected exception
    with user_pool_patch, client_meta_path, secret_hash_patch, boto3_patch:
        # Execute the function
        response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["message"] == "Tokens refreshed successfully."
    assert "authenticationResult" in response_body
    auth_result = response_body["authenticationResult"]
    assert auth_result["AccessToken"] == "new-access-token"
    assert auth_result["IdToken"] == "new-id-token"
    assert auth_result["idTokenExpires"] == 3600
    assert auth_result["accessTokenExpires"] == 3600
    assert auth_result["refreshTokenExpires"] == 30 * 24 * 60 * 60  # 30 days in seconds


@pytest.mark.unit
def test_lambda_handler_missing_refresh_token(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with missing refresh token.

    This test verifies that the lambda_handler function correctly handles the case
    when the refresh token is missing in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock with missing refresh token
    aws_event["body"] = json.dumps({"userId": "test-user-id"})

    # Execute the function
    response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Refresh token is required."


@pytest.mark.unit
def test_lambda_handler_missing_user_id(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with missing user ID.

    This test verifies that the lambda_handler function correctly handles the case
    when the user ID is missing in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock with missing user ID
    aws_event["body"] = json.dumps({"refreshToken": "test-refresh-token"})

    # Execute the function
    response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "User ID is required."


@pytest.mark.unit
def test_lambda_handler_invalid_refresh_token(
    aws_event: dict, lambda_context: MagicMock, mock_boto3_session: tuple, mock_env_vars: None
) -> None:
    """Test the lambda_handler function with an invalid refresh token.

    This test verifies that the lambda_handler function correctly handles the case
    when the provided refresh token is invalid or expired.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    aws_event["body"] = json.dumps({"refreshToken": "invalid-refresh-token", "userId": "test-user-id"})

    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Create the NotAuthorizedException
    cognito_client.initiate_auth.side_effect = botocore.exceptions.ClientError(
        {
            "Error": {
                "Code": "NotAuthorizedException",
                "Message": "Refresh token is invalid or expired.",
            }
        },
        "InitiateAuth",
    )

    # Mock the get_user_pool_id, get_client_metadata, and get_secret_hash functions
    user_pool_patch = patch.object(token_refresh, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_path = patch.object(
        token_refresh,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(token_refresh, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)

    with user_pool_patch, client_meta_path, secret_hash_patch, boto3_patch:
        # Execute the function
        response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 401
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "NotAuthorizedException has appeared" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_client_error(
    aws_event: dict, lambda_context: MagicMock, mock_boto3_session: tuple, mock_env_vars: None
) -> None:
    """Test the lambda_handler function with a client error.

    This test verifies that the lambda_handler function correctly handles the case
    when a client error occurs during token refresh.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    aws_event["body"] = json.dumps({"refreshToken": "test-refresh-token", "userId": "test-user-id"})

    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Create the ClientError
    client_error = botocore.exceptions.ClientError(
        {"Error": {"Code": "SomeError", "Message": "Some client error occurred."}},
        "initiate_auth",
    )

    # Mock the cognito_client to raise a ClientError
    cognito_client.initiate_auth.side_effect = client_error

    # Mock the get_user_pool_id, get_client_metadata, and get_secret_hash functions
    user_pool_patch = patch.object(token_refresh, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_path = patch.object(
        token_refresh,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(token_refresh, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)

    # Execute the function and assert it raises the expected exception
    with user_pool_patch, client_meta_path, secret_hash_patch, boto3_patch:
        # Execute the function
        response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Error refreshing tokens" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_general_exception(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a general exception.

    This test verifies that the lambda_handler function correctly handles unexpected
    exceptions during token refresh.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"refreshToken": "test-refresh-token", "userId": "test-user-id"})

    # Mock the get_user_pool_id function to raise an unexpected exception
    with patch.object(token_refresh, "get_user_pool_id", side_effect=Exception("Unexpected error")):
        # Execute the function
        response = token_refresh.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Error refreshing tokens" in response_body["error"]
