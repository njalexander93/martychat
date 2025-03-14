"""MartyChat Router for FastAPI.

Handles chatbot requests under `/api/v1/marty`.
"""

__author__ = ["Nikolai Alexander", "Doug Alexander"]
__email__ = "njalexander93@gmail.com, dalexander61@gmail.com"
__version__ = "1.0.0"
__date__ = "2025-02-28"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from typing import Any, cast

import boto3
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from utils.logger import logger

ENV = os.getenv("ENV", "development")
if ENV not in ["development", "production"]:
    logger.error("ENV environment variable must be either 'development' or 'production'")
    raise ValueError("ENV environment variable must be either 'development' or 'production'")
else:
    env_file = f".env.{ENV}"

logger.info("Loading environment variables from .env")
load_dotenv(".env")
if os.path.exists(env_file):
    logger.info(f"Loading environment variables from {env_file}")
    load_dotenv(env_file, override=True)
if os.path.exists(".env.local"):
    logger.info("Loading environment variables from .env.local")
    load_dotenv(".env.local", override=True)

router = APIRouter()
security = HTTPBearer()
token_auth = Security(security)

COGNITO_PUBLIC_KEYS: list[dict[str, Any]] = []


class ChatRequest(BaseModel):
    """Schema for chat API request."""

    message: str
    conversation_history: list = []


def set_cognito_public_keys(aws_region: str, cognito_user_pool_id: str) -> None:
    """Sets the global COGNITO_PUBLIC_KEYS variable.

    This function sets the global COGNITO_PUBLIC_KEYS variable by fetching the public keys from the Cognito User Pool.

    Args:
        aws_region (str): The AWS region where the Cognito User Pool is located.
        cognito_user_pool_id (str): The ID of the Cognito User Pool.
    """
    global COGNITO_PUBLIC_KEYS

    cognito_keys_url = f"https://cognito-idp.{aws_region}.amazonaws.com/{cognito_user_pool_id}/.well-known/jwks.json"
    response = requests.get(cognito_keys_url, timeout=10)
    COGNITO_PUBLIC_KEYS = response.json()["keys"]


def decode_token(token: str, header: dict, cognito_client_id: str, cognito_user_pool_id: str, aws_region: str) -> dict:
    """Decodes the user's token.

    This function decodes the user's token using the provided header and Cognito Client ID. It verifies the token's
    signature and audience. If the token is invalid, it raises an HTTPException.

    Args:
        token (str): The user's token.
        header (dict): The header of the token.
        cognito_client_id (str): The Cognito Client ID.
        cognito_user_pool_id (str): The Cognito User Pool ID.
        aws_region (str): The AWS region where the Cognito User Pool is located.

    Returns:
        dict: The decoded token.

    Raises:
        HTTPException: If the token is invalid.
    """
    # Get the public keys from the Cognito User Pool and find the key that matches the token
    if not COGNITO_PUBLIC_KEYS:
        set_cognito_public_keys(aws_region, cognito_user_pool_id)

    # Find the key that matches the token in the public keys and decode the token
    key: dict[str, Any] | RSAPublicKey | None = None
    for k in COGNITO_PUBLIC_KEYS:
        if k.get("kid") == header.get("kid"):
            key = k
            break
    if not key:
        raise HTTPException(status_code=403, detail="Invalid token key.")

    if isinstance(key, dict):
        key = cast(RSAPublicKey, jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key)))

    if not isinstance(key, RSAPublicKey):
        raise ValueError("Key must be an RSA public key.")

    decoded_token = jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=cognito_client_id,
    )

    return decoded_token


def verify_token(credentials: HTTPAuthorizationCredentials = token_auth) -> str:
    """Verifies the user's token.

    This function verifies the user's token by sending a request to the authentication service.

    Args:
        credentials (HTTPAuthorizationCredentials): The user's authentication credentials.

    Returns:
        str: The user's ID.

    Raises:
        HTTPException: If the token is invalid or missing.
    """
    token = credentials.credentials  # Get the token from the credentials

    cognito_user_param = os.getenv("COGNITO_USER_PARAM")
    cognito_client_param = os.getenv("COGNITO_CLIENT_PARAM")
    aws_region = os.getenv("REGION_NAME")
    if not cognito_user_param:
        logger.error("COGNITO_USER_PARAM environment variable is not set.")
        raise RuntimeError("COGNITO_USER_PARAM environment variable is not set.")
    if not cognito_client_param:
        logger.error("COGNITO_CLIENT_PARAM environment variable is not set.")
        raise RuntimeError("COGNITO_CLIENT_PARAM environment variable is not set.")
    if not aws_region:
        logger.error("REGION_NAME environment variable is not set.")
        raise RuntimeError("REGION_NAME environment variable is not set.")

    # Get the Cognito User Pool ID and Client ID from AWS Systems Manager Parameter Store
    session = boto3.session.Session()
    ssm = session.client("ssm")  # Client for AWS Systems Manager Parameter Store
    try:
        cognito_user_pool_id = ssm.get_parameter(Name=cognito_user_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("Error getting Cognito ID from AWS Systems Manager Parameter Store.")
        raise RuntimeError("Error getting Cognito ID from AWS Systems Manager Parameter Store.") from e
    try:
        cognito_client_id = ssm.get_parameter(Name=cognito_client_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("Error getting Cognito ID from AWS Systems Manager Parameter Store.")
        raise RuntimeError("Error getting Cognito ID from AWS Systems Manager Parameter Store.") from e

    try:
        header = jwt.get_unverified_header(token)

        # Find the key that matches the token in the public keys and decode the token
        decoded_token = decode_token(token, header, cognito_client_id, cognito_user_pool_id, aws_region)

        # Get the user ID from the token
        user_id = decoded_token.get("sub")
        if not user_id:
            logger.error("Token missing 'sub' claim.")
            raise HTTPException(status_code=403, detail="Invalid token structure.")

        return user_id
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=403, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=403, detail="Invalid token") from e


def analyze_query_complexity(message: str) -> int:
    """Calls the Lambda function to analyze query complexity.

    This function calls the Lambda function to analyze the query complexity.

    Args:
        message (str): The user's message.

    Returns:
        int: The k-value.

    Raises:
        RuntimeError: If the Lambda URL is not set.
        RuntimeError: If the k-value is not returned from the Lambda function.
    """
    # Make sure we have the lambda url in our environment variables.
    lambda_url = os.getenv("NEXT_PUBLIC_LAMBDA_URL")
    if not lambda_url:
        logger.error("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")
        raise RuntimeError("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")

    complexity_lambda_url = f"{lambda_url}/api/v1/analyze-query-complexity"
    logger.info("Querying %s with message: %s", complexity_lambda_url, message)
    response = requests.post(
        complexity_lambda_url,
        json={"message": message},
        headers={"Content-Type": "application/json", "Accept": "*/*"},
        timeout=30,
    )
    k = response.json().get("k")
    if not k:
        logger.error("Error getting query k-complexity from Lambda.")
        raise RuntimeError("Error getting query k-complexity from Lambda.")

    return k


def get_similar_docs(message: str, k: int, aws_parameters: dict) -> dict:
    """Calls the Lambda function to get similar documents.

    This function calls the Lambda function to get similar documents.

    Args:
        message (str): The user's message.
        k (int): The k-value.
        aws_parameters (dict): The AWS parameters.

    Returns:
        dict: The results from the Lambda function.

    Raises:
        RuntimeError: If the Lambda URL is not set.
    """
    # Make sure we have the lambda url in our environment variables.
    lambda_url = os.getenv("NEXT_PUBLIC_LAMBDA_URL")
    if not lambda_url:
        logger.error("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")
        raise RuntimeError("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")

    get_similar_doc_lambda_url = f"{lambda_url}/api/v1/get-similar-documents"
    logger.info(f"Querying {get_similar_doc_lambda_url} with message: {message}, and k-value: {k}")
    response = requests.post(
        get_similar_doc_lambda_url,
        json={
            "message": message,
            "k": k,
            "aws_parameters": {
                "api_secrets_param": aws_parameters["api_secrets_param"],
                "pinecone_env_param": aws_parameters["pinecone_env_param"],
                "pinecone_index_param": aws_parameters["pinecone_index_param"],
            },
        },
        headers={"Content-Type": "application/json", "Accept": "*/*"},
    )
    logger.info(f"Response from Lambda: {response.json()}")
    results = response.json()
    if not results:
        logger.error("Error getting similar documents from Lambda.")
        raise RuntimeError("Error getting similar documents from Lambda.")

    return results


def get_context_from_matches(matches: list) -> str:
    """Extracts the context from the matches.

    This function extracts the context from the matches.

    Args:
        matches (list): The matches from the Lambda function.

    Returns:
        str: The context from the matches.
    """
    contexts = []
    for match in matches:
        if match["score"] >= 0.45:
            contexts.append(match["content"])
    return "\n\n".join(contexts)


def generate_response_with_citations(message: str, contexts: str, citations: dict, aws_parameters: dict) -> dict:
    """Calls the Lambda function to generate a response with citations.

    This function calls the Lambda function to generate a response with citations.

    Args:
        message (str): The user's message.
        contexts (str): The context from the matches.
        citations (dict): The citations.
        aws_parameters (dict): The AWS parameters.

    Returns:
        dict: The response generated

    Raises:
        RuntimeError: If the Lambda URL is not set.
    """
    # Make sure we have the lambda url in our environment variables.
    lambda_url = os.getenv("NEXT_PUBLIC_LAMBDA_URL")
    if not lambda_url:
        logger.error("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")
        raise RuntimeError("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")

    generate_response_with_citations_lambda_url = f"{lambda_url}/api/v1/generate-response-with-citations"
    logger.info(f"Querying {generate_response_with_citations_lambda_url}.")
    response = requests.post(
        generate_response_with_citations_lambda_url,
        json={
            "message": message,
            "context": contexts,
            "citations": citations,
            "aws_parameters": {"api_secrets_param": aws_parameters["api_secrets_param"]},
        },
        headers={"Content-Type": "application/json", "Accept": "*/*"},
    )
    results = response.json()

    return {"response": results["response"]}


@router.post("/marty")
def generate_response(request: ChatRequest) -> dict:
    """Processes user input with history and citation support.

    This endpoint processes a user's question with historical context and citation support. It generates a response
    based on the provided context and citations. The response is generated using an AI model that follows specific
    guidelines for academic and research discussions.

    Args:
        request (ChatRequest): The request containing the user's question and user ID.

    Returns:
        dict: The response generated by the AI model.
    """
    try:
        request_metadata = request.dict()

        message = request_metadata["message"]
        conversation_history = request_metadata["conversation_history"]
    except Exception as e:
        logger.error(f"Error processing request: {e!s}")
        raise HTTPException(status_code=400, detail="Invalid request format") from e

    # Add the conversation history to the message to enhance the question before submitting it to the model.
    if conversation_history:
        formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        enhanced_message = f"Context from the previous conversation:\n{formatted_history}"
        enhanced_message += f"\nCurrent Question: {message}"
    else:
        enhanced_message = message

    # Analyze the query complexity using a Lambda function.
    try:
        k = analyze_query_complexity(enhanced_message)
    except Exception as e:
        logger.error(f"Error analyzing query complexity: {e!s}")
        raise HTTPException(status_code=500, detail="Error analyzing query complexity") from e

    aws_parameters = {
        "api_secrets_param": os.getenv("API_SECRETS_PARAM"),
        "pinecone_env_param": os.getenv("PINECONE_ENV_PARAM"),
        "pinecone_index_param": os.getenv("PINECONE_INDEX_PARAM"),
    }
    if not aws_parameters["api_secrets_param"]:
        raise RuntimeError("API_SECRETS_PARAM environment variable is required")
    if not aws_parameters["pinecone_env_param"]:
        raise RuntimeError("PINECONE_ENV_PARAM environment variable is required")
    if not aws_parameters["pinecone_index_param"]:
        raise RuntimeError("PINECONE_INDEX_PARAM environment variable is required")

    # Get enhanced document retrieval with deduplication and improved citation formatting
    try:
        results = get_similar_docs(enhanced_message, k, aws_parameters)
    except Exception as e:
        logger.error(f"Error getting similar documents: {e!s}")
        raise HTTPException(status_code=500, detail="Error getting similar documents") from e

    # Extract content and citations
    try:
        citations = results["citations"]
        contexts = get_context_from_matches(results["matches"])
    except KeyError as e:
        logger.error(f"Unable to locate '{e!s}' in the response from Lambda.")
        raise HTTPException(status_code=500, detail="Error extracting content and citations") from e

    # Generate a response with citations
    try:
        return generate_response_with_citations(message, contexts, citations, aws_parameters)
    except Exception as e:
        logger.error(f"Error generating response: {e!s}")
        raise HTTPException(status_code=500, detail="Error generating response") from e
