"""Tests for the get_similar_documents lambda function.

This module contains tests for the get_similar_documents lambda function in the backend/lambda directory.
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

import pytest

# Add the lambda directory to the sys path
lambda_path = os.path.join(os.path.dirname(__file__), "../../../lambda")
sys.path.insert(0, lambda_path)

# These imports depend on the sys.path modification above
import get_similar_documents  # noqa: E402


@pytest.mark.unit
def test_get_api_parameters(mock_boto3_session: tuple, mock_env_vars: None) -> None:
    """Test the get_api_parameters function.

    This test verifies that the get_api_parameters function correctly retrieves the API key
    and other parameters from AWS Secrets Manager and Parameter Store.

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
    ssm_client.get_parameter.side_effect = lambda **kwargs: {
        "Parameter": {
            "Value": (
                "secret-id"
                if kwargs["Name"] == "api_secrets_param"
                else "pinecone-env"
                if kwargs["Name"] == "pinecone_env_param"
                else "pinecone-index"
            )
        }
    }

    # Set up the mock responses for the Secrets Manager client
    secrets_manager_client.get_secret_value.return_value = {
        "SecretString": json.dumps(
            {"openai_api_key": "test-api-key", "openai_org_id": "test-org-id", "pinecone_api_key": "test-pinecone-key"}
        )
    }

    # Call the function
    aws_parameters = {
        "api_secrets_param": "api_secrets_param",
        "pinecone_env_param": "pinecone_env_param",
        "pinecone_index_param": "pinecone_index_param",
    }
    with patch("boto3.session.Session", return_value=mock_session):
        result = get_similar_documents.get_api_parameters(aws_parameters)

    # Assert the expected result
    assert result == {
        "openai_api_key": "test-api-key",
        "openai_org_id": "test-org-id",
        "pinecone_api_key": "test-pinecone-key",
        "pinecone_env": "pinecone-env",
        "pinecone_index": "pinecone-index",
    }
    assert ssm_client.get_parameter.call_count == 3


@pytest.mark.unit
def test_init_pinecone_index(mock_env_vars: None) -> None:
    """Test the init_pinecone_index function.

    This test verifies that the init_pinecone_index function correctly initializes the Pinecone index.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock Pinecone
    mock_pinecone = MagicMock()
    mock_index = MagicMock()
    mock_pinecone.return_value.Index.return_value = mock_index

    # Call the function
    with patch("get_similar_documents.Pinecone", mock_pinecone):
        result = get_similar_documents.init_pinecone_index("test-api-key", "test-env", "test-index")

    # Assert the expected result
    assert result == mock_index
    mock_pinecone.assert_called_once_with(api_key="test-api-key", environment="test-env")
    mock_pinecone.return_value.Index.assert_called_once_with("test-index")


@pytest.mark.unit
def test_preprocess_message() -> None:
    """Test the preprocess_message function.

    This test verifies that the preprocess_message function correctly enhances the query
    through basic text preprocessing and domain-specific augmentation.
    """
    # Sample message
    message = "What is the impact of learned helplessness on depression?"

    # Expected terms from psychology terms
    expected_terms = [
        "impact",
        "learned",
        "learning",
        "conditioning",
        "acquired",  # Extended from "learned"
        "helplessness",
        "depression",
    ]

    # Call the function
    result = get_similar_documents.preprocess_message(message)

    # Assert the expected result
    for term in expected_terms:
        assert term in result.split()
    # Check that stopwords are removed
    assert "is" not in result.split()
    assert "the" not in result.split()
    assert "of" not in result.split()
    assert "on" not in result.split()


@pytest.mark.unit
@patch("get_similar_documents.retry_operation", lambda max_retries: lambda func: func)  # Skip retries for testing
def test_get_embeddings_batch(mock_env_vars: None) -> None:
    """Test the get_embeddings_batch function.

    This test verifies that the get_embeddings_batch function correctly retrieves
    embeddings for a batch of search queries from the OpenAI API.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock OpenAI client
    mock_openai_client = MagicMock()
    mock_openai_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2, 0.3]), MagicMock(embedding=[0.4, 0.5, 0.6])]
    )

    # Sample search queries
    search_queries = ["query1", "query2"]

    # Call the function
    result = get_similar_documents.get_embeddings_batch(mock_openai_client, search_queries)

    # Assert the expected result
    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]
    assert result[1] == [0.4, 0.5, 0.6]
    mock_openai_client.embeddings.create.assert_called_once_with(
        model=get_similar_documents.OPENAI_EMBEDDING_MODEL, input=search_queries
    )


@pytest.mark.unit
@patch("get_similar_documents.retry_operation", lambda max_retries: lambda func: func)  # Skip retries for testing
def test_query_pinecone_index(mock_env_vars: None) -> None:
    """Test the query_pinecone_index function.

    This test verifies that the query_pinecone_index function correctly queries the
    Pinecone index for similar documents based on the provided embedding.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Mock Pinecone index
    mock_pinecone_index = MagicMock()
    mock_pinecone_index.query.return_value = {"matches": [{"id": "doc1", "score": 0.9}]}

    # Sample embedding
    embedding = [0.1, 0.2, 0.3]

    # Call the function
    result = get_similar_documents.query_pinecone_index(mock_pinecone_index, embedding, 5)

    # Assert the expected result
    assert result == {"matches": [{"id": "doc1", "score": 0.9}]}
    mock_pinecone_index.query.assert_called_once_with(vector=embedding, top_k=5, include_metadata=True)


@pytest.mark.unit
def test_format_citation_date() -> None:
    """Test the format_citation_date function.

    This test verifies that the format_citation_date function correctly formats the
    date string in the citation to a more readable format.
    """
    # Test with D:YYYYMMDDHHmmSS format
    assert get_similar_documents.format_citation_date("D:20230405123456") == "2023"

    # Test with a plain year
    assert get_similar_documents.format_citation_date("2023") == "2023"

    # Test with an invalid format
    assert get_similar_documents.format_citation_date("invalid") == "n.d."


@pytest.mark.unit
def test_deduplicate_documents() -> None:
    """Test the deduplicate_documents function.

    This test verifies that the deduplicate_documents function correctly deduplicates
    similar documents based on the title.
    """
    # Sample documents
    documents = [
        {
            "id": "doc1",
            "score": 0.9,
            "metadata": {"title": "Title A", "content": "Content A", "author": "Author A", "year": "2023"},
        },
        {
            "id": "doc2",
            "score": 0.8,
            "metadata": {"title": "Title B", "content": "Content B", "author": "Author B", "year": "2023"},
        },
        {
            "id": "doc3",
            "score": 0.95,  # Higher score than doc1
            "metadata": {
                "title": "Title A",  # Same title as doc1
                "content": "Better Content A",
                "author": "Author A",
                "year": "2023",
            },
        },
    ]

    # Call the function
    result = get_similar_documents.deduplicate_documents(documents)

    # Assert the expected result
    assert len(result) == 2  # Should have two documents after deduplication

    # Check that the document with higher score was kept for the duplicate title
    title_a_doc = next((doc for doc in result if doc["citation_info"]["title"] == "Title A"), None)
    assert title_a_doc is not None
    assert title_a_doc["score"] == 0.95
    assert title_a_doc["content"] == "Better Content A"

    # Check that the other document was also kept
    title_b_doc = next((doc for doc in result if doc["citation_info"]["title"] == "Title B"), None)
    assert title_b_doc is not None
    assert title_b_doc["score"] == 0.8
    assert title_b_doc["content"] == "Content B"


@pytest.mark.unit
def test_lambda_handler_success(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with successful document retrieval.

    This test verifies that the lambda_handler function correctly retrieves similar documents
    based on a query.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "What is learned helplessness?",
            "k": 5,
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Mock the required functions
    api_params_patch = patch.object(
        get_similar_documents,
        "get_api_parameters",
        return_value={
            "openai_api_key": "test-api-key",
            "openai_org_id": "test-org-id",
            "pinecone_api_key": "test-pinecone-key",
            "pinecone_env": "test-env",
            "pinecone_index": "test-index",
        },
    )

    # Mock Pinecone index initialization
    mock_index = MagicMock()
    pinecone_patch = patch.object(get_similar_documents, "init_pinecone_index", return_value=mock_index)

    # Mock OpenAI embeddings generation
    embeddings_patch = patch.object(
        get_similar_documents,
        "get_embeddings_batch",
        return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9], [0.1, 0.2, 0.3]],
    )

    # Mock Pinecone index query results
    mock_index.query.return_value = {
        "matches": [
            {
                "id": "doc1",
                "score": 0.9,
                "metadata": {"title": "Title A", "content": "Content A", "author": "Author A", "year": "2023"},
            }
        ]
    }

    # Mock document deduplication
    deduplicate_patch = patch.object(
        get_similar_documents,
        "deduplicate_documents",
        return_value=[
            {
                "score": 0.9,
                "content": "Content A",
                "citation_info": {"author": "Author A", "year": "2023", "title": "Title A"},
            }
        ],
    )

    # Execute the function
    with api_params_patch, pinecone_patch, embeddings_patch, deduplicate_patch:
        response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 200
    response_body = json.loads(response["body"])
    assert "matches" in response_body
    assert "citations" in response_body
    assert len(response_body["matches"]) == 1
    assert response_body["matches"][0]["score"] == 0.9
    assert response_body["matches"][0]["content"] == "Content A"
    assert "[1]" in response_body["citations"]


@pytest.mark.unit
def test_lambda_handler_missing_message(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a missing message.

    This test verifies that the lambda_handler function correctly handles a missing message
    in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event with missing message
    aws_event["body"] = json.dumps(
        {
            # Missing message
            "k": 5,
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Execute the function
    response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "Message is required" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_missing_k(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a missing k value.

    This test verifies that the lambda_handler function correctly handles a missing k value
    in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event with missing k
    aws_event["body"] = json.dumps(
        {
            "message": "What is learned helplessness?",
            # Missing k
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Execute the function
    response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "k is required" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_missing_aws_parameters(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with missing AWS parameters.

    This test verifies that the lambda_handler function correctly handles missing AWS parameters
    in the request body.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event with missing AWS parameters
    aws_event["body"] = json.dumps(
        {
            "message": "What is learned helplessness?",
            "k": 5,
            # Missing aws_parameters
        }
    )

    # Execute the function
    response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "AWS parameters are required" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_openai_api_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with an OpenAI API error.

    This test verifies that the lambda_handler function correctly handles an error
    when getting embeddings from OpenAI.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "What is learned helplessness?",
            "k": 5,
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Mock the required functions
    api_params_patch = patch.object(
        get_similar_documents,
        "get_api_parameters",
        return_value={
            "openai_api_key": "test-api-key",
            "openai_org_id": "test-org-id",
            "pinecone_api_key": "test-pinecone-key",
            "pinecone_env": "test-env",
            "pinecone_index": "test-index",
        },
    )

    pinecone_patch = patch.object(get_similar_documents, "init_pinecone_index", return_value=MagicMock())

    # Mock get_embeddings_batch to raise an exception
    embeddings_patch = patch.object(
        get_similar_documents,
        "get_embeddings_batch",
        side_effect=RuntimeError("An error occurred while getting embeddings from OpenAI."),
    )

    # Execute the function
    with api_params_patch, pinecone_patch, embeddings_patch:
        response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "An error occurred" in response_body["error"]


@pytest.mark.unit
def test_lambda_handler_pinecone_error(aws_event: dict, lambda_context: MagicMock, mock_env_vars: None) -> None:
    """Test the lambda_handler function with a Pinecone error.

    This test verifies that the lambda_handler function correctly handles an error
    when querying the Pinecone index.

    Args:
        aws_event (dict): The AWS event.
        lambda_context (MagicMock): The Lambda context.
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up the mock event
    aws_event["body"] = json.dumps(
        {
            "message": "What is learned helplessness?",
            "k": 5,
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Mock the required functions
    api_params_patch = patch.object(
        get_similar_documents,
        "get_api_parameters",
        return_value={
            "openai_api_key": "test-api-key",
            "openai_org_id": "test-org-id",
            "pinecone_api_key": "test-pinecone-key",
            "pinecone_env": "test-env",
            "pinecone_index": "test-index",
        },
    )

    mock_index = MagicMock()
    pinecone_patch = patch.object(get_similar_documents, "init_pinecone_index", return_value=mock_index)

    embeddings_patch = patch.object(get_similar_documents, "get_embeddings_batch", return_value=[[0.1, 0.2, 0.3]])

    # Mock query_pinecone_index to raise an exception
    query_patch = patch.object(
        get_similar_documents,
        "query_pinecone_index",
        side_effect=RuntimeError("An error occurred while querying the Pinecone index."),
    )

    # Execute the function
    with api_params_patch, pinecone_patch, embeddings_patch, query_patch:
        response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
    assert "An error occurred" in response_body["error"]


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
            "message": "What is learned helplessness?",
            "k": 5,
            "aws_parameters": {
                "api_secrets_param": "test-param",
                "pinecone_env_param": "test-env-param",
                "pinecone_index_param": "test-index-param",
            },
        }
    )

    # Mock the get_api_parameters function to raise an exception
    with patch.object(get_similar_documents, "get_api_parameters", side_effect=Exception("Unexpected error")):
        # Execute the function
        response = get_similar_documents.lambda_handler(aws_event, lambda_context)

    # Assert the expected result
    assert response["statusCode"] == 500
    response_body = json.loads(response["body"])
    assert "error" in response_body
