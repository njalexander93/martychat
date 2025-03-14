"""Tests for the analyze_query_complexity lambda function.

This module contains tests for the analyze_query_complexity lambda function in the backend/lambda directory. The tests
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

lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import analyze_query_complexity  # noqa: E402
import pytest  # noqa: E402


@pytest.mark.unit
def test_lambda_handler_basic_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with a basic query.

    This test function tests the lambda_handler function with a basic query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps({"message": "What is learned helplessness?"})

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    print("response_body: ", response_body)
    assert response["statusCode"] == 200
    assert "k" in response_body
    assert response_body["k"] == 5


@pytest.mark.unit
def test_lambda_handler_specific_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with a specific query.

    This test function tests the lambda_handler function with a specific query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps({"message": "What are the specific experiments that Seligman conducted?"})

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert "k" in response_body
    assert response_body["k"] == 3


@pytest.mark.unit
def test_lambda_handler_comparison_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with a comparison query.

    This test function tests the lambda_handler function with a comparison query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps({"message": "Compare learned helplessness to learned optimism."})

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert "k" in response_body
    assert response_body["k"] == 7


@pytest.mark.unit
def test_lambda_handler_theory_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with a theory query.

    This test function tests the lambda_handler function with a theory query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps({"message": "Give me an introduction to the theory of the psychology of happiness."})

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert "k" in response_body
    assert response_body["k"] == 7


@pytest.mark.unit
def test_lambda_handler_long_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with a long query.

    This test function tests the lambda_handler function with a long query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps(
        {
            "message": "What are the implications of learned helplessness on depression treatment,"
            + " and how has Seligman's research influenced modern therapeutic approaches for"
            + " addressing negative thought patterns and behavioral symptoms associated with"
            + " clinical depression?"
        }
    )

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert "k" in response_body
    assert response_body["k"] == 9


@pytest.mark.unit
def test_lambda_handler_no_query(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with no query.

    This test function tests the lambda_handler function with no query. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    aws_event["body"] = json.dumps({"message": ""})

    response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    response_body = json.loads(response["body"])
    assert response["statusCode"] == 500
    assert "error" in response_body


@pytest.mark.unit
def test_lambda_handler_internal_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: MagicMock) -> None:
    """Test the lambda_handler function with an internal error.

    This test function tests the lambda_handler function with an internal error. The function should return a response
    with the correct status code and body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (MagicMock): The mock environment variables.
    """
    # Arrange
    aws_event["body"] = json.dumps({"message": "Hello World!"})

    # Mock an exception during processing
    with patch.object(analyze_query_complexity, "logger") as mock_logger:
        mock_logger.info.side_effect = Exception("Test exception")

        # Act
        response = analyze_query_complexity.lambda_handler(aws_event, lambda_context)

    # Assert
    response_body = json.loads(response["body"])
    assert response["statusCode"] == 500
    assert "error" in response_body
