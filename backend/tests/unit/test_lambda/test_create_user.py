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
from unittest.mock import MagicMock, patch

import botocore
import pytest

# Add the lambda directory to the sys path
lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import create_user  # noqa: E402


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
    result = create_user.get_user_pool_id()

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
        result = create_user.get_client_metadata()

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
    result = create_user.get_secret_hash(username, client_id, client_secret)

    # Assert the result is not empty (we don't check the exact value because it's a hash)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.unit
def test_create_cognito_user_success(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the create_cognito_user function with a successful user creation.

    This test verifies that the create_cognito_user function correctly creates a new user
    in the AWS Cognito user pool.

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
    cognito_client.admin_create_user.return_value = {
        "User": {"Username": "test@example.com", "Attributes": [{"Name": "sub", "Value": "test-user-id"}]}
    }
    cognito_client.admin_initiate_auth.return_value = {
        "ChallengeName": "NEW_PASSWORD_REQUIRED",
        "Session": "test-session",
    }
    cognito_client.admin_respond_to_auth_challenge.return_value = {"AuthenticationResult": {"IdToken": "test-id-token"}}

    # Mock the AWS functions
    user_pool_patch = patch.object(create_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_patch = patch.object(
        create_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(create_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)
    # Apply all patches
    with user_pool_patch, client_meta_patch, secret_hash_patch, boto3_patch:
        # Execute the function
        result = create_user.create_cognito_user(
            {"email": "test@example.com", "password": "Test1234!", "first_name": "Test", "last_name": "User"}
        )

    # Assert the expected result
    assert result == "test-user-id"
    cognito_client.admin_create_user.assert_called_once()
    cognito_client.admin_initiate_auth.assert_called_once()
    cognito_client.admin_respond_to_auth_challenge.assert_called_once()


@pytest.mark.unit
def test_create_cognito_user_already_exists(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the create_cognito_user function when the user already exists.

    This test verifies that the create_cognito_user function correctly handles the case
    when the user already exists in the AWS Cognito user pool.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    cognito_client = MagicMock()

    # Mock the boto3 session
    mock_session.client.return_value = cognito_client

    # Mock the cognito_client to raise a UsernameExistsException
    # username_exists_exception = boto3.client("cognito-idp").exceptions.UsernameExistsException(
    #     {"Error": {"Code": "UsernameExistsException", "Message": "User already exists."}}, "admin_create_user"
    # )
    # cognito_client.admin_create_user.side_effect = username_exists_exception

    # Create a correct exception type for UsernameExistsException
    username_exists_exception = botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "UsernameExistsException", "Message": "User already exists."}},
        operation_name="admin_create_user",
    )

    # Add the exceptions namespace to the cognito_client mock
    cognito_client.exceptions = MagicMock()
    cognito_client.exceptions.UsernameExistsException = type("UsernameExistsException", (Exception,), {})

    # Set up the side effect
    cognito_client.admin_create_user.side_effect = username_exists_exception

    # Mock the AWS functions and a raised RuntimeError.
    user_pool_patch = patch.object(create_user, "get_user_pool_id", return_value="test-user-pool-id")
    client_meta_path = patch.object(
        create_user,
        "get_client_metadata",
        return_value={"cognito_client_id": "test-client-id", "cognito_client_secret": "test-client-secret"},
    )
    secret_hash_patch = patch.object(create_user, "get_secret_hash", return_value="test-secret-hash")
    boto3_patch = patch("boto3.client", return_value=cognito_client)
    runtime_error = pytest.raises(RuntimeError, match="User already exists.")

    # Execute the function and assert it raises the expected exception
    with user_pool_patch, client_meta_path, secret_hash_patch, boto3_patch, runtime_error:
        create_user.create_cognito_user(
            {"email": "test@example.com", "password": "Test1234!", "first_name": "Test", "last_name": "User"}
        )

    # Assert the expected calls
    cognito_client.admin_create_user.assert_called_once()
    cognito_client.admin_initiate_auth.assert_not_called()
    cognito_client.admin_respond_to_auth_challenge.assert_not_called()


@pytest.mark.unit
def test_add_user_to_dynamodb(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the add_user_to_dynamodb function.

    This test verifies that the add_user_to_dynamodb function correctly adds a user
    to the DynamoDB users table.

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

    # User data for the test
    user_data = {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "organization": "Test Organization",
        "created_at": "2023-01-01T00:00:00",
        "last_login": "2023-01-01T00:00:00",
    }

    boto3_session_patch = patch("boto3.session.Session", return_value=mock_session)
    ssm_client_path = patch("boto3.client", return_value=ssm_client)
    dynamodb_resource_patch = patch("boto3.resource", return_value=dynamodb_resource)

    # Execute the function
    with boto3_session_patch, ssm_client_path, dynamodb_resource_patch:
        create_user.add_user_to_dynamodb(user_data)

    # Assert the expected calls
    ssm_client.get_parameter.assert_called_once_with(Name="/path/to/dynamodb/user/table")
    dynamodb_resource.Table.assert_called_once_with("test-table-name")
    table.put_item.assert_called_once_with(Item=user_data)


@pytest.mark.unit
def test_lambda_handler_success(
    aws_event: dict, lambda_context: MagicMock, mock_boto3_session: tuple, mock_env_vars: None
) -> None:
    """Test the lambda_handler function with a successful user creation.

    This test verifies that the lambda_handler function correctly creates a new user
    in the AWS Cognito user pool and adds the user to the DynamoDB users table.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps(
        {
            "email": "test@example.com",
            "password": "Test1234!",
            "firstName": "Test",
            "lastName": "User",
            "organization": "Test Organization",
        }
    )

    # Mock the create_cognito_user and add_user_to_dynamodb functions
    create_cognito_user_patch = patch.object(create_user, "create_cognito_user", return_value="test-user-id")
    add_user_to_dynamodb_patch = patch.object(create_user, "add_user_to_dynamodb", return_value=None)
    with create_cognito_user_patch, add_user_to_dynamodb_patch:
        # Execute the function
        response = create_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 201
    response_body = json.loads(response["body"])
    assert response_body["message"] == "User created successfully!"
    assert response_body["user"] == "test-user-id"


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
            "email": "test@example.com",
            "password": "Test1234!",
            # Missing firstName and lastName
            "organization": "Test Organization",
        }
    )

    # Execute the function
    response = create_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "Missing required fields."


@pytest.mark.unit
def test_lambda_handler_user_already_exists(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function when the user already exists.

    This test verifies that the lambda_handler function correctly handles the case
    when the user already exists in the AWS Cognito user pool.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    aws_event["body"] = json.dumps(
        {
            "email": "test@example.com",
            "password": "Test1234!",
            "firstName": "Test",
            "lastName": "User",
            "organization": "Test Organization",
        }
    )

    # Mock the create_cognito_user function to raise a RuntimeError
    with patch.object(create_user, "create_cognito_user", side_effect=RuntimeError("User already exists.")):
        # Execute the function
        response = create_user.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 400
    response_body = json.loads(response["body"])
    assert response_body["error"] == "User already exists."
