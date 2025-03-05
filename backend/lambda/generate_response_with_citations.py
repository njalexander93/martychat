"""Lambda function to generate an enhanced response with citations.

This Lambda function generates an enhanced response to a user query by incorporating citations and a structured format.
The response is designed to be professional, informative, and engaging. The function uses the OpenAI API to generate the
response based on the provided context, message, and citations.
"""

__author__ = ["Nikolai Alexander", "Doug Alexander"]
__email__ = "njalexander93@gmail.com, dalexander61@gmail.com"
__version__ = "1.0.0"
__date__ = "2025-02-28"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import json
import logging
import os
import time
from typing import TYPE_CHECKING

import boto3
from openai import APIConnectionError, APIError, OpenAI, RateLimitError

if TYPE_CHECKING:
    from openai.types import ChatCompletionMessageParam


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Only use StreamHandler for CloudWatch
)
logger = logging.getLogger(__name__)
if os.getenv("ENV", "production") == "development":
    logger.setLevel(logging.DEBUG)

# Set the CORS headers for the response
CORS_HEADERS = {
    "Content-Type": "application/json",
    "X-Custom-Header": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS, GET, POST, PUT, PATCH, DELETE",
    "Access-Control-Allow-Headers": "X-Requested-With, content-type",
    "Access-Control-Allow-Credentials": "true",  # Required for credentials-based requests
}

PROMPT = (
    "Based solely on the provided context, give a detailed and constructive response that highlights the value "
    + "and contributions of the work. Do not include any information from outside the provided context. "
)

REQUIREMENTS = """1. Draw exclusively from the provided context
2. Present the information in a positive, appreciative manner
3. Use formal, professional language
4. Include relevant citations for all claims
5. If certain aspects cannot be addressed from the available context, acknowledge this professionally
"""


def get_api_parameters(aws_parameters: dict) -> dict:
    """Function for retrieving the OpenAI API key and organization ID from AWS Secrets Manager.

    This function retrieves the OpenAI API key and organization ID from AWS Secrets Manager. The function assumes that
    the secrets are stored in the format of a JSON object with the keys "openai_api_key" and "openai_org_id".

    Args:
        aws_parameters (str): The AWS parameters containing the API secrets and Pinecone environment.

    Returns:
        dict: The OpenAI API key and organization ID.
    """
    session = boto3.session.Session()
    secrets_manager = session.client("secretsmanager")
    ssm = session.client("ssm")

    api_secrets_param = aws_parameters.get("api_secrets_param")

    if not api_secrets_param:
        raise RuntimeError("api_secrets_param is required in the AWS parameters.")

    try:
        secret_id = ssm.get_parameter(Name=api_secrets_param, WithDecryption=True)["Parameter"]["Value"]
        secret_key = secrets_manager.get_secret_value(SecretId=secret_id)
        secrets = json.loads(secret_key["SecretString"])

        return {"openai_api_key": secrets["openai_api_key"], "openai_org_id": secrets["openai_org_id"]}
    except Exception as e:
        logger.exception("An error occurred while retrieving the API secrets: %s", e)
        raise RuntimeError("Failed to retrieve the API secrets.") from e


def format_citations(citations: dict) -> str:
    """Function for formatting citations in the prompt.

    This function formats the citations with deduplication and clear formatting.

    Args:
        citations (dict): A dictionary of citations with citation IDs as keys and citation strings as values.

    Returns:
        str: The formatted citations.
    """
    # Create a dictionary of unique sources
    unique_sources = {}
    for cid, source in citations.items():
        source_key = source.strip().lower()
        if source_key not in unique_sources:
            unique_sources[source_key] = cid

    # Format citations using only unique sources
    formatted_citations = []
    for _, cid in unique_sources.items():
        original_source = citations[cid]
        formatted_citations.append(f"{cid}: {original_source}")

    return "\n".join(formatted_citations)


def get_enhanced_system_prompt() -> str:
    """Function for getting the enhanced system prompt from AWS S3.

    This function retrieves the enhanced system prompt from AWS S3. The prompt is used to provide additional context
    to the OpenAI API for generating responses.

    Returns:
        str: The enhanced system prompt.
    """
    session = boto3.session.Session()
    s3 = session.client("s3")

    bucket_name = os.getenv("S3_PROMPTS_BUCKET")
    if not bucket_name:
        raise RuntimeError("S3_PROMPTS_BUCKET environment variable is required.")

    try:
        response = s3.get_object(Bucket=bucket_name, Key="marty.txt")
        enhanced_prompt = response["Body"].read().decode("utf-8")
        logger.info("Successfully retrieved the enhanced system prompt from S3.")
        return enhanced_prompt
    except Exception as e:
        logger.exception("An error occurred while retrieving the enhanced system prompt: %s", e)
        raise RuntimeError("Failed to retrieve the enhanced system prompt.") from e


def get_openai_response(client: OpenAI, prompt: str, citations: dict) -> str:
    """Function to generate a response from the OpenAI API.

    This function generates a response from the OpenAI API based on the provided prompt.

    Args:
        client (OpenAI): The OpenAI API client.
        prompt (str): The prompt to send to the OpenAI API.
        citations (dict): A dictionary of citations with citation IDs as keys and citation strings as values.

    Returns:
        str: The response generated by the OpenAI API.
    """
    # Create the messages for the OpenAI API
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": get_enhanced_system_prompt()},
        {"role": "user", "content": prompt},
    ]

    # Format the citations for inclusion in the response
    citations_text = ""
    if citations:
        citations_text = "\n\nReferences:\n"
        citations_text += "\n".join(f"{cid}: {source}" for cid, source in citations.items())

    # Allow for 3 retries to contact the OpenAI API for any type of connection error.
    retry_count = 0
    max_retries = 3
    while retry_count <= max_retries:
        try:
            # Send the request to the OpenAI API and get the response.
            response = client.chat.completions.create(model="gpt-4", messages=messages, temperature=0.7)
            response_text = response.choices[0].message.content or ""

            # Add the citations to the response if they are not already present in the response.
            if citations and "References:" not in response_text:
                response_text += citations_text

            return response_text
        except (RuntimeError, APIError, APIConnectionError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise e

            wait_time = 2**retry_count
            logger.warning(
                "Hit a %s error while trying to get a response from OpenAI. Retrying in %s seconds.",
                e.__class__.__name__,
                wait_time,
            )
            logger.warning("Error message: %s", e)
            time.sleep(wait_time)

    # Fallback to ensure the function always returns if we've exhausted all retries or other unexpected issues
    raise RuntimeError("Failed to get a response from OpenAI after multiple attempts")


def lambda_handler(event: dict, context: object) -> dict:
    """Function to generate an enhanced response that handles conversation flow.

    This function generates an enhanced response to a user query by incorporating citations and a structured format. The
    response is designed to be professional, informative, and engaging.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response data to return to the user.
    """
    try:
        body = json.loads(event["body"])
        message = body["message"]
        context = body["context"]
        citations = body["citations"]
        aws_parameters = body["aws_parameters"]

        # Get the OpenAI API parameters from AWS and create the OpenAI client.
        api_parameters = get_api_parameters(aws_parameters)
        openai_client = OpenAI(api_key=api_parameters["openai_api_key"], organization=api_parameters["openai_org_id"])

        # Format the citations for inclusion in the prompt
        formatted_citations = format_citations(citations)

        # Create the enhanced prompt for the OpenAI API
        prompt = PROMPT
        prompt += f"\n\nContext: {context}"
        prompt += f"\n\nQuestion: {message}"
        prompt += f"\n\nRequirements:\n{REQUIREMENTS}"
        prompt += f"Available Citations:\n{formatted_citations}"

        try:
            response = get_openai_response(openai_client, prompt, citations)
            return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps({"response": response})}
        except RateLimitError as e:
            logger.error("Rate limit exceeded while generating the response: %s", e)
            return {
                "statusCode": 429,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Rate limit exceeded. Please try again later."}),
            }
    except Exception as e:
        logger.error("An error occurred while generating the response: %s", e)
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": json.dumps({"error": str(e)})}
