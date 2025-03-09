"""Tests for the MartyChat Router in marty.py.

This module contains tests for the MartyChat router defined in backend/marty/marty.py.
The tests verify correct authentication handling, route functionality, and external service integration.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import sys
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add the backend directory to the sys path
backend_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.insert(0, backend_dir)

# These imports depend on the sys.path modification above
from marty import marty  # noqa: E402


@pytest.mark.unit
def test_set_cognito_public_keys(mock_env_vars: None) -> None:
    """Test the set_cognito_public_keys function.

    This test verifies that the set_cognito_public_keys function correctly retrieves
    and sets the Cognito public keys.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock the requests.get method to return a known response
    mock_response = MagicMock()
    mock_response.json.return_value = {"keys": [{"kid": "test-kid", "alg": "RS256"}]}

    with patch("marty.marty.requests.get", return_value=mock_response) as mock_get:
        # Call the function
        marty.set_cognito_public_keys("us-east-1", "test-user-pool-id")

        # Verify the public keys were set correctly
        assert [{"kid": "test-kid", "alg": "RS256"}] == marty.COGNITO_PUBLIC_KEYS

        # Verify the requests.get method was called with the correct URL
        mock_get.assert_called_once_with(
            "https://cognito-idp.us-east-1.amazonaws.com/test-user-pool-id/.well-known/jwks.json", timeout=10
        )


@pytest.mark.unit
def test_decode_token_valid_token(mock_env_vars: None) -> None:
    """Test the decode_token function with a valid token.

    This test verifies that the decode_token function correctly decodes a valid token.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_token = "valid-token"
    test_header = {"kid": "test-kid"}
    test_client_id = "test-client-id"
    test_user_pool_id = "test-user-pool-id"
    test_region = "us-east-1"

    # Mock the global COGNITO_PUBLIC_KEYS
    marty.COGNITO_PUBLIC_KEYS = [{"kid": "test-kid", "kty": "RSA"}]

    # Mock the jwt.algorithms.RSAAlgorithm.from_jwk function
    mock_rsa_key = MagicMock(spec=RSAPublicKey)

    # Mock the jwt.decode function
    mock_decoded_token = {"sub": "test-user-id", "client_id": test_client_id}

    mock_from_jwk = patch("marty.marty.jwt.algorithms.RSAAlgorithm.from_jwk", return_value=mock_rsa_key)
    mock_jwt_decode = patch("marty.marty.jwt.decode", return_value=mock_decoded_token)

    with mock_from_jwk, mock_jwt_decode:
        # Call the function
        result = marty.decode_token(test_token, test_header, test_client_id, test_user_pool_id, test_region)

        # Verify the result
        assert result == mock_decoded_token

        # Verify jwt.decode was called with the correct parameters
        marty.jwt.decode.assert_called_once_with(
            test_token, key=mock_rsa_key, algorithms=["RS256"], audience=test_client_id
        )


@pytest.mark.unit
def test_decode_token_invalid_key(mock_env_vars: None) -> None:
    """Test the decode_token function with an invalid key.

    This test verifies that the decode_token function correctly raises an exception
    when the token key is invalid.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_token = "valid-token"
    test_header = {"kid": "invalid-kid"}  # Different from the one in COGNITO_PUBLIC_KEYS
    test_client_id = "test-client-id"
    test_user_pool_id = "test-user-pool-id"
    test_region = "us-east-1"

    # Mock the global COGNITO_PUBLIC_KEYS
    marty.COGNITO_PUBLIC_KEYS = [{"kid": "test-kid", "kty": "RSA"}]

    # Call the function and expect an HTTPException
    with pytest.raises(HTTPException) as excinfo:
        marty.decode_token(test_token, test_header, test_client_id, test_user_pool_id, test_region)

    # Verify the exception details
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Invalid token key."


@pytest.mark.unit
def test_decode_token_jwt_exception(mock_env_vars: None) -> None:
    """Test the decode_token function when jwt.decode raises an exception.

    This test verifies that the decode_token function correctly handles exceptions from
    the jwt.decode function.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_token = "invalid-token"
    test_header = {"kid": "test-kid"}
    test_client_id = "test-client-id"
    test_user_pool_id = "test-user-pool-id"
    test_region = "us-east-1"

    # Mock the global COGNITO_PUBLIC_KEYS
    marty.COGNITO_PUBLIC_KEYS = [{"kid": "test-kid", "kty": "RSA"}]

    # Mock the jwt.algorithms.RSAAlgorithm.from_jwk function
    mock_rsa_key = MagicMock(spec=RSAPublicKey)

    # Set up the patches
    mock_from_jwk = patch("marty.marty.jwt.algorithms.RSAAlgorithm.from_jwk", return_value=mock_rsa_key)
    mock_jwt_decode = patch("marty.marty.jwt.decode", side_effect=jwt.InvalidTokenError("Invalid token"))

    # Call the function and expect an InvalidTokenError
    with mock_from_jwk, mock_jwt_decode, pytest.raises(jwt.InvalidTokenError):
        marty.decode_token(test_token, test_header, test_client_id, test_user_pool_id, test_region)


@pytest.mark.unit
def test_verify_token_valid_token(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the verify_token function with a valid token.

    This test verifies that the verify_token function correctly validates a token
    and returns the user ID.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_token = "valid-token"
    test_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=test_token)
    test_user_id = "test-user-id"

    # Mock the jwt.get_unverified_header function
    test_header = {"kid": "test-kid"}

    # Mock the decode_token function
    mock_decoded_token = {"sub": test_user_id}

    # Set up mocks for SSM and Secrets Manager
    mock_session, _ = mock_boto3_session
    ssm_client = MagicMock()
    mock_session.client.return_value = ssm_client

    # Mock SSM parameter store responses
    ssm_client.get_parameter.side_effect = lambda **kwargs: {
        "Parameter": {
            "Value": "test-pool-id" if kwargs["Name"] == "/path/to/cognito_user_pool_id" else "test-client-id"
        }
    }

    # Set up the patches
    with (
        patch("marty.marty.jwt.get_unverified_header", return_value=test_header) as mock_get_header,
        patch("marty.marty.decode_token", return_value=mock_decoded_token) as mock_decode,
    ):
        # Call the function
        result = marty.verify_token(test_credentials)

        # Verify the result
        assert result == test_user_id

        # Use the mock objects for assertions
        mock_get_header.assert_called_once_with(test_token)
        mock_decode.assert_called_once_with(test_token, test_header, "test-client-id", "test-pool-id", "us-east-1")


@pytest.mark.unit
def test_verify_token_expired_token(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the verify_token function with an expired token.

    This test verifies that the verify_token function correctly raises an exception
    when the token is expired.

    Args:
        mock_boto3_session (tuple): The mocked boto3 session and client.
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_token = "expired-token"
    test_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=test_token)

    # Mock the jwt.get_unverified_header function
    test_header = {"kid": "test-kid"}

    # Set up mocks for SSM and Secrets Manager
    mock_session, _ = mock_boto3_session
    ssm_client = MagicMock()
    mock_session.client.return_value = ssm_client

    # Mock SSM parameter store responses
    ssm_client.get_parameter.side_effect = lambda **kwargs: {
        "Parameter": {
            "Value": "test-pool-id" if kwargs["Name"] == "/path/to/cognito_user_pool_id" else "test-client-id"
        }
    }

    # Set up the patches
    mock_get_header = patch("marty.marty.jwt.get_unverified_header", return_value=test_header)
    mock_decode = patch("marty.marty.decode_token", side_effect=jwt.ExpiredSignatureError("Token expired"))

    # Call the function and expect an HTTPException
    with mock_get_header, mock_decode, pytest.raises(HTTPException) as excinfo:
        marty.verify_token(test_credentials)

    # Verify the exception details
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Token expired"


@pytest.mark.unit
def test_analyze_query_complexity(mock_env_vars: None) -> None:
    """Test the analyze_query_complexity function.

    This test verifies that the analyze_query_complexity function correctly calls the
    Lambda function and returns the k-value.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock the requests.post method to return a known response
    mock_response = MagicMock()
    mock_response.json.return_value = {"k": 5}

    with patch("marty.marty.requests.post", return_value=mock_response) as mock_post:
        # Call the function
        result = marty.analyze_query_complexity("What is learned helplessness?")

        # Verify the result
        assert result == 5

        # Use mock object for assertions
        mock_post.assert_called_once_with(
            "http://localhost:9000/api/v1/analyze-query-complexity",
            json={"message": "What is learned helplessness?"},
            headers={"Content-Type": "application/json", "Accept": "*/*"},
            timeout=30,
        )


@pytest.mark.unit
def test_analyze_query_complexity_error(mock_env_vars: None) -> None:
    """Test the analyze_query_complexity function when the Lambda function returns an error.

    This test verifies that the analyze_query_complexity function correctly raises an exception
    when the Lambda function fails.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock the requests.post method to return a response without a k value
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "An error occurred"}

    post_patch = patch("marty.marty.requests.post", return_value=mock_response)
    runtime_error_patch = pytest.raises(RuntimeError, match="Error getting query k-complexity from Lambda.")

    with post_patch, runtime_error_patch:
        marty.analyze_query_complexity("What is learned helplessness?")


@pytest.mark.unit
def test_get_similar_docs(mock_env_vars: None) -> None:
    """Test the get_similar_docs function.

    This test verifies that the get_similar_docs function correctly calls the
    Lambda function and returns the results.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_message = "What is learned helplessness?"
    test_k = 5
    test_aws_params = {
        "api_secrets_param": "/path/to/api_secrets",
        "pinecone_env_param": "/path/to/pinecone_env",
        "pinecone_index_param": "/path/to/pinecone_index",
    }

    # Expected results from the Lambda function
    test_results = {
        "matches": [{"content": "Content about learned helplessness", "score": 0.95}],
        "citations": {"[1]": "Seligman (1975). Learned Helplessness"},
    }

    # Mock the requests.post method to return a known response
    mock_response = MagicMock()
    mock_response.json.return_value = test_results

    with patch("marty.marty.requests.post", return_value=mock_response) as mock_post:
        # Call the function
        result = marty.get_similar_docs(test_message, test_k, test_aws_params)

        # Verify the result
        assert result == test_results

        # Use the mock reference
        mock_post.assert_called_once_with(
            "http://localhost:9000/api/v1/get-similar-documents",
            json={"message": test_message, "k": test_k, "aws_parameters": test_aws_params},
            headers={"Content-Type": "application/json", "Accept": "*/*"},
        )


@pytest.mark.unit
def test_get_context_from_matches() -> None:
    """Test the get_context_from_matches function.

    This test verifies that the get_context_from_matches function correctly extracts
    the context from the matches based on the score threshold.
    """
    # Sample matches
    matches = [
        {"score": 0.9, "content": "High-scoring content"},
        {"score": 0.6, "content": "Medium-scoring content"},
        {"score": 0.4, "content": "Low-scoring content below threshold"},
    ]

    # Call the function
    result = marty.get_context_from_matches(matches)

    # Verify the result
    assert "High-scoring content" in result
    assert "Medium-scoring content" in result
    assert "Low-scoring content below threshold" not in result
    assert result == "High-scoring content\n\nMedium-scoring content"


@pytest.mark.unit
def test_generate_response_with_citations(mock_env_vars: None) -> None:
    """Test the generate_response_with_citations function.

    This test verifies that the generate_response_with_citations function correctly calls the
    Lambda function and returns the response.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_message = "What is learned helplessness?"
    test_contexts = "Context about learned helplessness"
    test_citations = {"[1]": "Seligman (1975). Learned Helplessness"}
    test_aws_params = {"api_secrets_param": "/path/to/api_secrets"}

    # Expected response from the Lambda function
    test_response = {"response": "Response about learned helplessness"}

    # Mock the requests.post method to return a known response
    mock_response = MagicMock()
    mock_response.json.return_value = test_response

    with patch("marty.marty.requests.post", return_value=mock_response) as mock_post:
        # Call the function
        result = marty.generate_response_with_citations(test_message, test_contexts, test_citations, test_aws_params)

        # Verify the result
        assert result == {"response": "Response about learned helplessness"}

        # Use the mock reference
        mock_post.assert_called_once_with(
            "http://localhost:9000/api/v1/generate-response-with-citations",
            json={
                "message": test_message,
                "context": test_contexts,
                "citations": test_citations,
                "aws_parameters": test_aws_params,
            },
            headers={"Content-Type": "application/json", "Accept": "*/*"},
        )


@pytest.mark.unit
def test_generate_response_route_successful_request(mock_env_vars: None) -> None:
    """Test the generate_response route handler with a successful request.

    This test verifies that the generate_response function correctly processes a request
    and returns a response.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    # Mock the analyze_query_complexity function
    mock_k = 5

    # Mock the get_similar_docs function
    mock_results = {
        "matches": [{"content": "Content about learned helplessness", "score": 0.95}],
        "citations": {"[1]": "Seligman (1975). Learned Helplessness"},
    }

    # Mock the get_context_from_matches function
    mock_context = "Context about learned helplessness"

    # Mock the generate_response_with_citations function
    mock_response = {"response": "Response about learned helplessness"}

    # Set up the patches
    mock_analyze = patch("marty.marty.analyze_query_complexity", return_value=mock_k)
    mock_get_docs = patch("marty.marty.get_similar_docs", return_value=mock_results)
    mock_get_context = patch("marty.marty.get_context_from_matches", return_value=mock_context)
    mock_generate = patch("marty.marty.generate_response_with_citations", return_value=mock_response)

    # Apply all the mocks
    with mock_analyze, mock_get_docs, mock_get_context, mock_generate:
        # Call the function
        result = marty.generate_response(test_request)

        # Verify the result
        assert result == {"response": "Response about learned helplessness"}


@pytest.mark.unit
def test_generate_response_route_with_conversation_history(mock_env_vars: None) -> None:
    """Test the generate_response route handler with conversation history.

    This test verifies that the generate_response function correctly processes a request
    with conversation history.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data with conversation history
    test_request = MagicMock()
    test_request.dict.return_value = {
        "message": "What is learned helplessness?",
        "conversation_history": [
            {"role": "user", "content": "Tell me about Seligman."},
            {
                "role": "chatbot",
                "content": "Martin Seligman is a psychologist known for his work on learned helplessness.",
            },
        ],
    }

    # Set up the patches
    mock_analyze = patch("marty.marty.analyze_query_complexity")
    mock_get_docs = patch("marty.marty.get_similar_docs", return_value={"matches": [], "citations": {}})
    mock_get_context = patch("marty.marty.get_context_from_matches", return_value="")
    mock_generate = patch("marty.marty.generate_response_with_citations", return_value={"response": "test"})

    # Apply all the mocks
    with mock_analyze as analyze_mock, mock_get_docs, mock_get_context, mock_generate:
        # Call the function
        marty.generate_response(test_request)

        # Get the enhanced message that was passed to analyze_query_complexity
        enhanced_message = analyze_mock.call_args[0][0]

        # Verify the enhanced message includes the conversation history
        assert "Context from the previous conversation" in enhanced_message
        assert "user: Tell me about Seligman." in enhanced_message
        assert (
            "chatbot: Martin Seligman is a psychologist known for his work on learned helplessness." in enhanced_message
        )
        assert "Current Question: What is learned helplessness?" in enhanced_message


@pytest.mark.unit
def test_generate_response_missing_api_params(mock_env_vars: None) -> None:
    """Test the generate_response route handler when API parameters are missing.

    This test verifies that the generate_response function correctly raises an exception
    when required environment variables are missing.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    env_patch = patch.dict(os.environ, {"API_SECRETS_PARAM": ""}, clear=False)
    analyze_query_patch = patch("marty.marty.analyze_query_complexity", return_value=5)
    get_similar_docs_patch = patch("marty.marty.get_similar_docs", return_value={"matches": [], "citations": {}})
    generate_response_patch = patch(
        "marty.marty.generate_response_with_citations", return_value={"message": "Test response"}
    )
    runtime_error_patch = pytest.raises(RuntimeError, match="API_SECRETS_PARAM environment variable is required")

    # Call the function and expect a RuntimeError
    with env_patch, analyze_query_patch, get_similar_docs_patch, generate_response_patch, runtime_error_patch:
        marty.generate_response(test_request)


@pytest.mark.unit
def test_generate_response_error_in_analyze_complexity(mock_env_vars: None) -> None:
    """Test the generate_response route handler when analyze_query_complexity fails.

    This test verifies that the generate_response function correctly handles errors
    from the analyze_query_complexity function.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    # Mock the analyze_query_complexity function to raise an exception
    mock_analyze = patch(
        "marty.marty.analyze_query_complexity", side_effect=RuntimeError("Failed to analyze query complexity")
    )

    # Call the function and expect an HTTPException
    with mock_analyze, pytest.raises(HTTPException) as excinfo:
        marty.generate_response(test_request)

    # Verify the exception details
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Error analyzing query complexity"


@pytest.mark.unit
def test_generate_response_error_in_get_similar_docs(mock_env_vars: None) -> None:
    """Test the generate_response route handler when get_similar_docs fails.

    This test verifies that the generate_response function correctly handles errors
    from the get_similar_docs function.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    # Set up the patches
    mock_analyze = patch("marty.marty.analyze_query_complexity", return_value=5)
    mock_get_docs = patch("marty.marty.get_similar_docs", side_effect=RuntimeError("Failed to get similar documents"))

    # Call the function and expect an HTTPException
    with mock_analyze, mock_get_docs, pytest.raises(HTTPException) as excinfo:
        marty.generate_response(test_request)

    # Verify the exception details
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Error getting similar documents"


@pytest.mark.unit
def test_generate_response_missing_matches_key(mock_env_vars: None) -> None:
    """Test the generate_response route handler when 'matches' key is missing.

    This test verifies that the generate_response function correctly handles missing
    'matches' key in the response from get_similar_docs.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    # Set up the patches
    mock_analyze = patch("marty.marty.analyze_query_complexity", return_value=5)
    mock_get_docs = patch("marty.marty.get_similar_docs", return_value={"citations": {}})

    # Call the function and expect an HTTPException
    with mock_analyze, mock_get_docs, pytest.raises(HTTPException) as excinfo:
        marty.generate_response(test_request)

    # Verify the exception details
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Error extracting content and citations"


@pytest.mark.unit
def test_generate_response_error_in_generate_with_citations(mock_env_vars: None) -> None:
    """Test the generate_response route handler when generate_response_with_citations fails.

    This test verifies that the generate_response function correctly handles errors
    from the generate_response_with_citations function.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock data
    test_request = MagicMock()
    test_request.dict.return_value = {"message": "What is learned helplessness?", "conversation_history": []}

    # Set up the patches
    mock_analyze = patch("marty.marty.analyze_query_complexity", return_value=5)
    mock_get_docs = patch("marty.marty.get_similar_docs", return_value={"matches": [], "citations": {}})
    mock_get_context = patch("marty.marty.get_context_from_matches", return_value="context")
    mock_generate = patch(
        "marty.marty.generate_response_with_citations", side_effect=RuntimeError("Failed to generate response")
    )

    # Call the function and expect an HTTPException
    with mock_analyze, mock_get_docs, mock_get_context, mock_generate, pytest.raises(HTTPException) as excinfo:
        marty.generate_response(test_request)

    # Verify the exception details
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Error generating response"
