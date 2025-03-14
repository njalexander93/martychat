"""Tests for the delete_user lambda function.

This module contains tests for the delete_user lambda function in the backend/lambda directory. The tests
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
import delete_user  # noqa: E402


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
    result = delete_user.get_user_pool_id()

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
        result = delete_user.get_client_metadata()

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
    result = delete_user.get_secret_hash(username, client_id, client_secret)

    # Assert the result is not empty (we don't check the exact value because it's a hash)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.unit
def test_delete_user_from_cognito_success(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the delete_user_from_cognito function with successful user deletion.

    This test verifies that the delete_user_from_cognito function correctly deletes a user
    from the AWS Cognito user pool.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Mock the cognito_client responses - admin_delete_user returns None on success
    cognito_client.admin_delete_user.return_value = None

    # Mock the AWS functions
    user_pool_patch = patch.object(delete_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_patch = patch.object(
        delete_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(delete_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)
    # Apply all patches
    with user_pool_patch, client_meta_patch, secret_hash_patch, boto3_patch:
        # Execute the function
        result = delete_user.delete_user_from_cognito("test@example.com")

    # Assert the expected result
    assert result is True
    cognito_client.admin_delete_user.assert_called_once_with(
        UserPoolId="test-user-pool-id",
        Username="test@example.com",
        ClientId="test-client-id",
        SecretHash="test-secret-hash",
    )


@pytest.mark.unit
def test_delete_user_from_cognito_user_not_found(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the delete_user_from_cognito function when the user is not found.

    This test verifies that the delete_user_from_cognito function correctly handles the case
    when the user does not exist in the AWS Cognito user pool.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Create a correct exception type for UsernameExistsException
    user_not_found_exception = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "UserNotFoundException", "Message": "User does not exist."}},
        operation_name="admin_delete_user",
    )

    # Add the exceptions namespace to the cognito_client mock
    cognito_client.exceptions = MagicMock()
    cognito_client.exceptions.UserNotFoundException = type("UserNotFoundException", (Exception,), {})

    # Mock the cognito_client to raise a UserNotFoundException
    cognito_client.admin_delete_user.side_effect = user_not_found_exception

    # Mock the AWS functions and a raised RuntimeError.
    user_pool_patch = patch.object(delete_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_path = patch.object(
        delete_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(delete_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)
    with user_pool_patch, client_meta_path, secret_hash_patch, boto3_patch:
        # Execute the function
        result = delete_user.delete_user_from_cognito("nonexistent@example.com")

    # Assert the expected result
    assert result is False
    cognito_client.admin_delete_user.assert_called_once()


@pytest.mark.unit
def test_delete_user_from_dynamodb_success(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the delete_user_from_dynamodb function with successful user deletion.

    This test verifies that the delete_user_from_dynamodb function correctly deletes a user
    from the DynamoDB users table.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    ssm_client = MagicMock()
    dynamodb_resource = MagicMock()
    table = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = ssm_client
    mock_session.resource.return_value = dynamodb_resource

    # Mock the SSM client
    dynamodb_resource.Table.return_value = table
    ssm_client.get_parameter.return_value = {"Parameter": {"Value": "test-table-name"}}

    # Mock the DynamoDB table
    table.get_item.return_value = {"Item": {"user_id": "test-user-id"}}
    table.delete_item.return_value = {}  # DynamoDB returns an empty dict on successful deletion

    # Execute the function
    boto3_session_patch = patch("boto3.session.Session", return_value=mock_session)
    ssm_client_path = patch("boto3.client", return_value=ssm_client)
    dynamodb_resource_patch = patch("boto3.resource", return_value=dynamodb_resource)
    with boto3_session_patch, ssm_client_path, dynamodb_resource_patch:
        result = delete_user.delete_user_from_dynamodb("test-user-id")

    # Assert the expected result
    assert result is True
    ssm_client.get_parameter.assert_called_once_with(Name="/path/to/dynamodb/user/table")
    dynamodb_resource.Table.assert_called_once_with("test-table-name")
    table.get_item.assert_called_once_with(Key={"user_id": "test-user-id"})
    table.delete_item.assert_called_once_with(Key={"user_id": "test-user-id"})


@pytest.mark.unit
def test_delete_user_from_dynamodb_user_not_found(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the delete_user_from_dynamodb function when the user is not found.

    This test verifies that the delete_user_from_dynamodb function correctly handles the case
    when the user does not exist in the DynamoDB users table.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    ssm_client = MagicMock()
    dynamodb_resource = MagicMock()
    table = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = ssm_client
    mock_session.resource.return_value = dynamodb_resource

    # Mock the SSM client
    dynamodb_resource.Table.return_value = table
    ssm_client.get_parameter.return_value = {"Parameter": {"Value": "test-table-name"}}

    # Mock the DynamoDB table - No Item key indicates user not found
    table.get_item.return_value = {}

    # Execute the function
    boto3_session_patch = patch("boto3.session.Session", return_value=mock_session)
    ssm_client_path = patch("boto3.client", return_value=ssm_client)
    dynamodb_resource_patch = patch("boto3.resource", return_value=dynamodb_resource)
    with boto3_session_patch, ssm_client_path, dynamodb_resource_patch:
        result = delete_user.delete_user_from_dynamodb("nonexistent-user-id")

    # Assert the expected result
    assert result is False
    ssm_client.get_parameter.assert_called_once_with(Name="/path/to/dynamodb/user/table")
    dynamodb_resource.Table.assert_called_once_with("test-table-name")
    table.get_item.assert_called_once_with(Key={"user_id": "nonexistent-user-id"})
    table.delete_item.assert_not_called()


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

    cognito_client.admin_get_user.return_value = {
        "Username": "test@example.com",
        "UserAttributes": [
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "sub", "Value": "test-user-id"},
        ],
    }

    user_pool_patch = patch.object(delete_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_patch = patch.object(
        delete_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(delete_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)

    with user_pool_patch, client_meta_patch, secret_hash_patch, boto3_patch:
        # Execute the function
        result = delete_user.get_user_id("test@example.com")

    # Assert the expected result
    assert result == "test-user-id"
    cognito_client.admin_get_user.assert_called_once_with(
        UserPoolId="test-user-pool-id",
        Username="test@example.com",
        ClientId="test-client-id",
        SecretHash="test-secret-hash",
    )


@pytest.mark.unit
def test_get_user_id_user_not_found(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_user_id function when the user is not found.

    This test verifies that the get_user_id function correctly handles the case
    when the user does not exist in the AWS Cognito user pool.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()
    mock_session.client.return_value = cognito_client

    # Create the UserNotFoundException
    user_not_found_exception = botocore.exceptions.ClientError(
        {"Error": {"Code": "UserNotFoundException", "Message": "User does not exist."}},
        "admin_get_user",
    )

    # Mock the cognito_client to raise a UserNotFoundException
    cognito_client.admin_get_user.side_effect = user_not_found_exception

    user_pool_patch = patch.object(delete_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_patch = patch.object(
        delete_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(delete_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)
    runtime_error = pytest.raises(RuntimeError, match="User test@example.com not found in AWS Cognito.")
    with user_pool_patch, client_meta_patch, secret_hash_patch, boto3_patch, runtime_error:
        delete_user.get_user_id("test@example.com")

    # Assert the expected calls
    cognito_client.admin_get_user.assert_called_once()


@pytest.mark.unit
def test_lambda_handler_success(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with successful user deletion.

    This test verifies that the lambda_handler function correctly deletes a user
    from both AWS Cognito and DynamoDB.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"username": "test@example.com"})

    # Mock the get_user_id, delete_user_from_cognito, and delete_user_from_dynamodb functions
    user_id_patch = patch.object(delete_user, "get_user_id", return_value="test-user-id")
    cognito_patch = patch.object(delete_user, "delete_user_from_cognito", return_value=True)
    dynamodb_patch = patch.object(delete_user, "delete_user_from_dynamodb", return_value=True)
    with user_id_patch, cognito_patch, dynamodb_patch:
        # Execute the function
        response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["message"] == "User deleted successfully."


@pytest.mark.unit
def test_lambda_handler_missing_username(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with missing username.

    This test verifies that the lambda_handler function correctly handles the case
    when the username is missing in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({})  # Empty request body

    # Execute the function
    response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Invalid request body."


@pytest.mark.unit
def test_lambda_handler_get_user_id_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function when get_user_id fails.

    This test verifies that the lambda_handler function correctly handles the case
    when the get_user_id function fails (user not found).

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"username": "nonexistent@example.com"})

    # Mock the get_user_id function to raise a RuntimeError
    with patch.object(delete_user, "get_user_id", side_effect=RuntimeError("User not found")):
        # Execute the function
        response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Internal Server Error"


@pytest.mark.unit
def test_lambda_handler_cognito_delete_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function when delete_user_from_cognito fails.

    This test verifies that the lambda_handler function correctly handles the case
    when the delete_user_from_cognito function fails (user not found).

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"username": "test@example.com"})

    # Mock the get_user_id function to return a user ID, but delete_user_from_cognito fails
    user_id_patch = patch.object(delete_user, "get_user_id", return_value="test-user-id")
    cognito_patch = patch.object(delete_user, "delete_user_from_cognito", return_value=False)
    with user_id_patch, cognito_patch:
        # Execute the function
        response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert response_body["error"] == "User not found."


@pytest.mark.unit
def test_lambda_handler_dynamodb_delete_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function when delete_user_from_dynamodb fails.

    This test verifies that the lambda_handler function correctly handles the case
    when the delete_user_from_dynamodb function fails (user not found).

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"username": "test@example.com"})

    # Mock the get_user_id and delete_user_from_cognito functions to succeed, but delete_user_from_dynamodb fails
    user_id_patch = patch.object(delete_user, "get_user_id", return_value="test-user-id")
    cognito_patch = patch.object(delete_user, "delete_user_from_cognito", return_value=True)
    dynamodb_patch = patch.object(delete_user, "delete_user_from_dynamodb", return_value=False)
    with user_id_patch, cognito_patch, dynamodb_patch:
        # Execute the function
        response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 404
    response_body = json.loads(response["body"])
    assert response_body["error"] == "User not found."


@pytest.mark.unit
def test_lambda_handler_runtime_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a runtime error.

    This test verifies that the lambda_handler function correctly handles unexpected runtime errors.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps({"username": "test@example.com"})

    # Mock the get_user_id function to raise a runtime error
    with patch.object(delete_user, "get_user_id", side_effect=Exception("Unexpected error")):
        # Execute the function
        response = delete_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Internal Server Error"
