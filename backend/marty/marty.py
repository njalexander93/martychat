"""MartyChat Router for FastAPI.

Handles chatbot requests under `/api/v1/marty`.
"""

__author__ = ["Nikolai Alexander", "Doug Alexander"]
__email__ = "njalexander93@gmail.com, dalexander61@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import jwt
import requests
import boto3
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from utils.logger import logger

ENV = os.getenv("ENV", "development")
if ENV not in ["development", "production"]:
    logger.error("ENV environment variable must be either 'development' or 'production'")
    raise ValueError("ENV environment variable must be either 'development' or 'production'")
else:
    env_file = f".env.{ENV}"

logger.info(f"Loading environment variables from .env")
load_dotenv(".env")
if os.path.exists(env_file):
    logger.info(f"Loading environment variables from {env_file}")
    load_dotenv(env_file, override=True)
if os.path.exists(".env.local"):
    logger.info(f"Loading environment variables from .env.local")
    load_dotenv(".env.local", override=True)

router = APIRouter()
security = HTTPBearer()

COGNITO_PUBLIC_KEYS = None

class ChatRequest(BaseModel):
    """Schema for chat API request."""
    message: str
    conversation_history: list = []

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verifies the user's token.

    This function verifies the user's token by sending a request to the authentication service.

    Args:
        credentials (HTTPAuthorizationCredentials): The user's authentication credentials.
    Returns:
        str: The user's ID.
    Raises:
        HTTPException: If the token is invalid or missing.
    """
    global COGNITO_PUBLIC_KEYS

    token = credentials.credentials # Get the token from the credentials

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
    ssm = session.client("ssm") # Client for AWS Systems Manager Parameter Store
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

        # Get the public keys from the Cognito User Pool and find the key that matches the token
        if not COGNITO_PUBLIC_KEYS:
            cognito_keys_url = f"https://cognito-idp.{aws_region}.amazonaws.com/{cognito_user_pool_id}/.well-known/jwks.json"
            response = requests.get(cognito_keys_url)
            COGNITO_PUBLIC_KEYS = response.json()["keys"]

        # Find the key that matches the token in the public keys and decode the token
        key = next((key for key in COGNITO_PUBLIC_KEYS if key["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=403, detail="Invalid token key.")
        decoded_token = jwt.decode(token, key=jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key)),
                                   algorithms=["RS256"], audience=cognito_client_id)

        # Get the user ID from the token
        user_id = decoded_token.get("sub")
        if not user_id:
            logger.error("Token missing 'sub' claim.")
            raise HTTPException(status_code=403, detail="Invalid token structure.")

        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

def format_citations(citations: dict) -> str:
    """Formats citations with deduplication and clear formatting.

    Given a dictionary of citation IDs and corresponding sources, this function deduplicates the sources and formats.

    Args:
        citations (dict): A dictionary of citation IDs and corresponding sources.
    Returns:
        str: The formatted citations with deduplication.
    """
    return " "

def generate_response_with_citations(question: str, context: str, system_prompt: str, citations: dict) -> str:
    """Generates a response with citations based on the provided context and question.

    Given a question, context, and citations, this function generates a response using an AI model and includes the
    provided citations.

    Args:
        question (str): The question asked by the user.
        context (str): The context from which the response should be generated.
        citations (dict): A dictionary of citation IDs and corresponding sources.
    Returns:
        str: The response generated by the AI model with citations.
    """

    prompt = f"""Based solely on the provided context, give a detailed and constructive response that highlights the value and contributions of the work. Do not include any information from outside the provided context.

    Context: {context}

    Question: {question}

    Requirements:
    1. Draw exclusively from the provided context
    2. Present the information in a positive, appreciative manner
    3. Use formal, professional language
    4. Include relevant citations for all claims
    5. If certain aspects cannot be addressed from the available context, acknowledge this professionally

    Available Citations:
    {format_citations(citations)}
    """
    return " "

@router.post("/marty")
def generate_response(request: ChatRequest, user_id: str = Depends(verify_token)) -> dict:
    """Processes user input with history and citation support.

    This endpoint processes a user's question with historical context and citation support. It generates a response
    based on the provided context and citations. The response is generated using an AI model that follows specific
    guidelines for academic and research discussions.

    Args:
        request (ChatRequest): The request containing the user's question and user ID.
    Returns:
        dict: The response generated by the AI model.
    """
    # Make sure we have the lambda url in our environment variables.
    lambda_url = os.getenv("NEXT_PUBLIC_LAMBDA_URL")
    if not lambda_url:
        logger.error("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")
        raise RuntimeError("NEXT_PUBLIC_LAMBDA_URL environment variable is not set.")
    logger.info(f"Using Lambda URL: {lambda_url}")

    try:
        request_metadata = request.dict()

        message = request_metadata["message"]
        conversation_history = request_metadata["conversation_history"]
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid request format")

    # Add the conversation history to the message to enhance the question before submitting it to the model.
    if conversation_history:
        formatted_history = "\n".join([f"{msg["role"]}: {msg["content"]}" for msg in conversation_history])
        enhanced_message = f"Context from the previous conversation:\n{formatted_history}"
        enhanced_message += f"\nCurrent Question: {message}"
    else:
        enhanced_message = message

    # Analyze the query complexity using a Lambda function.
    try:
        complexity_lambda_url = f"{lambda_url}/api/v1/analyze-query-complexity"
        logger.info(f"Querying {complexity_lambda_url} with message: {enhanced_message}")
        response = requests.post(
            complexity_lambda_url,
            json={"message": enhanced_message},
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*"
            }
        )
        k = response.json().get("k")
        if not k:
            logger.error("Error getting query k-complexity from Lambda.")
            raise RuntimeError("Error getting query k-complexity from Lambda.")
    except Exception as e:
        logger.error(f"Error analyzing query complexity: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing query complexity")


    api_secrets_param = os.getenv("API_SECRETS_PARAM")
    if not api_secrets_param:
        raise RuntimeError("API_SECRETS_PARAM environment variable is required")
    pinecone_env_param = os.getenv("PINECONE_ENV_PARAM")
    if not pinecone_env_param:
        raise RuntimeError("PINECONE_ENV_PARAM environment variable is required")
    pinecone_index_param = os.getenv("PINECONE_INDEX_PARAM")
    if not pinecone_index_param:
        raise RuntimeError("PINECONE_INDEX_PARAM environment variable is required")


    # Get enhanced document retrieval with deduplication and improved citation formatting
    try:
        get_similar_doc_lambda_url = f"{lambda_url}/api/v1/get-similar-documents"
        logger.info(f"Querying {get_similar_doc_lambda_url} with message: {enhanced_message}, and k-value: {k}")
        response = requests.post(
            get_similar_doc_lambda_url,
            json={
                "message": enhanced_message,
                "k": k,
                "aws_parameters": {
                    "api_secrets_param": api_secrets_param,
                    "pinecone_env_param": pinecone_env_param,
                    "pinecone_index_param": pinecone_index_param
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*"
            }
        )
        logger.info(f"Response from Lambda: {response.json()}")
        results = response.json()
        if not results:
            logger.error("Error getting similar documents from Lambda.")
            raise RuntimeError("Error getting similar documents from Lambda.")
    except Exception as e:
        logger.error(f"Error getting similar documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting similar documents")

    # Extract content and citations
    try:
        contexts = []
        citations = results["citations"]
        for match in results["matches"]:
            if match["score"] >= 0.45:
                contexts.append(f"{match['content']} {match['citation_id']}")
        combined_context = "\n\n".join(contexts)
    except KeyError as e:
        logger.error(f"Unable to locate '{str(e)}' in the response from Lambda.")
        raise HTTPException(status_code=500, detail="Error extracting content and citations")

    # Generate a response with citations
    try:
        generate_response_with_citations_lambda_url = f"{lambda_url}/api/v1/generate-response-with-citations"
        logger.info(f"Querying {generate_response_with_citations_lambda_url}.")
        response = requests.post(
            generate_response_with_citations_lambda_url,
            json={
                "message": enhanced_message,
                "context": combined_context,
                "citations": citations,
                "aws_parameters": {
                    "api_secrets_param": api_secrets_param
                }
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*"
            }
        )
        results = response.json()

        return {"response": results["response"]}
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating response")
