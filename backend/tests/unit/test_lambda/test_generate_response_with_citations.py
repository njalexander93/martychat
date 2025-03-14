"""Tests for the generate_response_with_citations lambda function.

This module contains tests for the generate_response_with_citations lambda function in the backend/lambda directory.
The tests are written using the pytest framework.
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

import httpx
import pytest
from openai import RateLimitError

# Add the lambda directory to the sys path
lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import generate_response_with_citations  # noqa: E402


@pytest.mark.unit
def test_get_api_parameters(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_api_parameters function.

    This test verifies that the get_api_parameters function correctly retrieves the OpenAI API key
    and organization ID from AWS Secrets Manager.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock responses
    mock_session, _ = mock_boto3_session
    ssm_client = MagicMock()
    secrets_manager_client = MagicMock()
    mock_session.client.side_effect = lambda service_name, **kwargs: {
        "ssm": ssm_client,
        "secretsmanager": secrets_manager_client,
    }.get(service_name, MagicMock())

    # Set up the mock responses for the SSM client
    ssm_client.get_parameter.return_value = {"Parameter": {"Value": "secret-id"}}

    # Set up the mock responses for the Secrets Manager client
    secrets_manager_client.get_secret_value.return_value = {
        "SecretString": json.dumps({"openai_api_key": "test-api-key", "openai_org_id": "test-org-id"})
    }

    # Call the function
    aws_parameters = {"api_secrets_param": "test-param"}
    with patch("boto3.session.Session", return_value=mock_session):
        result = generate_response_with_citations.get_api_parameters(aws_parameters)

    # Assert the expected result
    assert result == {"openai_api_key": "test-api-key", "openai_org_id": "test-org-id"}
    ssm_client.get_parameter.assert_called_once_with(Name="test-param", WithDecryption=True)
    secrets_manager_client.get_secret_value.assert_called_once_with(SecretId="secret-id")


@pytest.mark.unit
def test_format_citations() -> None:
    """Test the format_citations function.

    This test verifies that the format_citations function correctly formats the citations
    with deduplication and clear formatting.
    """
    # Sample citations
    citations = {
        "[1]": "Author A (2023). Title A",
        "[2]": "Author B (2023). Title B",
        "[3]": "author a (2023). title a",  # Duplicate of [1] with different case
    }

    # Call the function
    result = generate_response_with_citations.format_citations(citations)

    # Assert the expected result - should contain unique citations
    assert "[1]: Author A (2023). Title A" in result
    assert "[2]: Author B (2023). Title B" in result
    assert len(result.split("\n")) == 2  # Only two unique citations should be formatted


@pytest.mark.unit
def test_get_enhanced_system_prompt(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_enhanced_system_prompt function.

    This test verifies that the get_enhanced_system_prompt function correctly retrieves
    the enhanced system prompt from AWS S3.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock
    mock_session, _ = mock_boto3_session
    s3_client = MagicMock()
    mock_session.client.return_value = s3_client

    # Mock the S3 client response
    s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"This is the enhanced system prompt.")}

    # Call the function
    with patch("boto3.session.Session", return_value=mock_session):
        result = generate_response_with_citations.get_enhanced_system_prompt()

    # Assert the expected result
    assert result == "This is the enhanced system prompt."
    s3_client.get_object.assert_called_once_with(Bucket="s3-prompt-bucket", Key="marty.txt")


@pytest.mark.unit
def test_get_openai_response(mock_env_vars: None) -> None:
    """Test the get_openai_response function.

    This test verifies that the get_openai_response function correctly generates a response
    from the OpenAI API based on the provided prompt.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock the OpenAI client
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="This is the OpenAI response."))]
    )

    # Sample prompt and citations
    prompt = "Sample prompt"
    citations = {"[1]": "Author A (2023). Title A"}

    # Mock the get_enhanced_system_prompt function
    enhanced_system_prompt_patch = patch.object(
        generate_response_with_citations, "get_enhanced_system_prompt", return_value="Enhanced system prompt"
    )
    with enhanced_system_prompt_patch:
        # Call the function
        result = generate_response_with_citations.get_openai_response(mock_openai_client, prompt, citations)

    # Assert the expected result
    assert result == "This is the OpenAI response.\n\nReferences:\n[1]: Author A (2023). Title A"
    mock_openai_client.chat.completions.create.assert_called_once()
    # Verify the messages parameter contains the system prompt and user prompt
    called_args = mock_openai_client.chat.completions.create.call_args[1]
    assert len(called_args["messages"]) == 2
    assert called_args["messages"][0]["role"] == "system"
    assert called_args["messages"][0]["content"] == "Enhanced system prompt"
    assert called_args["messages"][1]["role"] == "user"
    assert called_args["messages"][1]["content"] == prompt


@pytest.mark.unit
def test_get_openai_response_with_references_in_response(mock_env_vars: None) -> None:
    """Test the get_openai_response function when the response already contains references.

    This test verifies that the get_openai_response function doesn't duplicate references
    when they are already present in the response.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock the OpenAI client
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="This is the OpenAI response.\n\nReferences:\n[1] Some citation"))]
    )

    # Sample prompt and citations
    prompt = "Sample prompt"
    citations = {"[1]": "Author A (2023). Title A"}

    # Mock the get_enhanced_system_prompt function
    enhanced_system_prompt_patch = patch.object(
        generate_response_with_citations, "get_enhanced_system_prompt", return_value="Enhanced system prompt"
    )
    with enhanced_system_prompt_patch:
        # Call the function
        result = generate_response_with_citations.get_openai_response(mock_openai_client, prompt, citations)

    # Assert the expected result should not duplicate references
    assert result == "This is the OpenAI response.\n\nReferences:\n[1] Some citation"
    assert "References:" in result
    assert result.count("References:") == 1  # Only one "References:" section


@pytest.mark.unit
def test_lambda_handler_success(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with successful response generation.

    This test verifies that the lambda_handler function correctly generates an enhanced response
    with citations based on the provided prompt and context.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "Sample message",
            "context": "Sample context",
            "citations": {"[1]": "Author A (2023). Title A"},
            "aws_parameters": {"api_secrets_param": "test-param"},
        }
    )

    # Mock the required functions
    api_params_patch = patch.object(
        generate_response_with_citations,
        "get_api_parameters",
        return_value={"openai_api_key": "test-api-key", "openai_org_id": "test-org-id"},
    )
    openai_response_patch = patch.object(
        generate_response_with_citations,
        "get_openai_response",
        return_value="This is the enhanced response with citations.",
    )
    format_citations_patch = patch.object(
        generate_response_with_citations, "format_citations", return_value="[1]: Author A (2023). Title A"
    )

    # Execute the function
    with api_params_patch, openai_response_patch, format_citations_patch:
        response = generate_response_with_citations.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert response_body["response"] == "This is the enhanced response with citations."


@pytest.mark.unit
def test_lambda_handler_rate_limit_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a rate limit error from OpenAI.

    This test verifies that the lambda_handler function correctly handles rate limit errors from OpenAI.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "Sample message",
            "context": "Sample context",
            "citations": {"[1]": "Author A (2023). Title A"},
            "aws_parameters": {"api_secrets_param": "test-param"},
        }
    )

    # Mock the required functions
    api_params_patch = patch.object(
        generate_response_with_citations,
        "get_api_parameters",
        return_value={"openai_api_key": "test-api-key", "openai_org_id": "test-org-id"},
    )
    format_citations_patch = patch.object(
        generate_response_with_citations, "format_citations", return_value="[1]: Author A (2023). Title A"
    )

    # Mock OpenAI client creation
    mock_openai = MagicMock()
    openai_patch = patch("openai.OpenAI", return_value=mock_openai)

    # Create a mock HTTP response
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 429  # HTTP 429 Too Many Requests
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {"Retry-After": "60"}

    # Raise a RateLimitError when get_openai_response is called
    get_openai_response_patch = patch.object(
        generate_response_with_citations,
        "get_openai_response",
        side_effect=RateLimitError(message="Rate limit exceeded", response=mock_response, body="Rate limit exceeded"),
    )

    # Execute the function
    with api_params_patch, format_citations_patch, openai_patch, get_openai_response_patch:
        response = generate_response_with_citations.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 429
    response_body = json.loads(response["body"])
    assert "Rate limit exceeded" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_missing_parameters(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with missing parameters.

    This test verifies that the lambda_handler function correctly handles missing parameters
    in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event with missing parameters
    aws_event["body"] = json.dumps(
        {
            # Missing "message"
            "context": "Sample context",
            "citations": {"[1]": "Author A (2023). Title A"},
            "aws_parameters": {"api_secrets_param": "test-param"},
        }
    )

    # Execute the function
    response = generate_response_with_citations.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body


@pytest.mark.unit
def test_lambda_handler_general_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a general error.

    This test verifies that the lambda_handler function correctly handles unexpected errors.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "Sample message",
            "context": "Sample context",
            "citations": {"[1]": "Author A (2023). Title A"},
            "aws_parameters": {"api_secrets_param": "test-param"},
        }
    )

    # Mock the get_api_parameters function to raise an exception
    general_exception_patch = patch.object(
        generate_response_with_citations, "get_api_parameters", side_effect=Exception("Unexpected error")
    )

    with general_exception_patch:
        # Execute the function
        response = generate_response_with_citations.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
