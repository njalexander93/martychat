"""Lambda function to generate an enhanced response with citations

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

import os
import json
import logging
import time
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
import boto3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()] # Only use StreamHandler for CloudWatch
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
    "Access-Control-Allow-Credentials": "true"  # Required for credentials-based requests
}

# TODO: Move this all to S3
ENHANCED_SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in presenting research and academic work in a constructive and positive manner. When discussing Seligman's work:

1. Focus on his contributions, insights, and the positive impact of his research
2. Present his theories and findings in an appreciative, professional tone
3. Use ONLY information provided in the context - do not reference external knowledge
4. If asked about topics not covered in the provided context, politely indicate that the information is not available in the current document set
5. Maintain academic rigor while highlighting the strengths and value of the work

Format your response with:
- Clear structure and logical flow
- Professional, formal language
- Full sentences and well-developed paragraphs
- Proper citation integration
"""

PROMPT = "Based solely on the provided context, give a detailed and constructive response that highlights the value and contributions of the work. Do not include any information from outside the provided context."

REQUIREMENTS = """1. Draw exclusively from the provided context
2. Present the information in a positive, appreciative manner
3. Use formal, professional language
4. Include relevant citations for all claims
5. If certain aspects cannot be addressed from the available context, acknowledge this professionally
"""

def get_api_parameters(aws_parameters: str) -> dict:
    """Function for retrieving the OpenAI API key and organization ID from AWS Secrets Manager.

    This function retrieves the OpenAI API key and organization ID from AWS Secrets Manager. The function assumes that the secrets are stored in the

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

        return {
            "openai_api_key": secrets["openai_api_key"],
            "openai_org_id": secrets["openai_org_id"]
        }
    except Exception as e:
        logger.exception("An error occurred while retrieving the API secrets: %s", e)
        raise RuntimeError("Failed to retrieve the API secrets.") from e

def format_citations(citations: dict) -> str:
    """Function for formatting citations in the prompt

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
    for source_key, cid in unique_sources.items():
        original_source = citations[cid]
        formatted_citations.append(f"{cid}: {original_source}")

    return "\n".join(formatted_citations)

def get_openai_response(client: OpenAI, prompt: str, citations: dict) -> str:
    """Function to generate a response from the OpenAI API

    This function generates a response from the OpenAI API based on the provided prompt.

    Args:
        client (OpenAI): The OpenAI API client.
        prompt (str): The prompt to send to the OpenAI API.
    Returns:
        str: The response generated by the OpenAI API.
    """

    # Create the messages for the OpenAI API
    messages = [
        {"role": "system", "content": ENHANCED_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
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
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7
            )
            response_text = response.choices[0].message.content

            # Add the citations to the response if they are not already present in the response.
            if citations and "References:" not in response_text:
                response_text += citations_text

            return response_text
        except (RuntimeError, APIError, APIConnectionError) as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise e

            wait_time = 2 ** retry_count
            logger.warning("Hit a %s error while trying to get a response from OpenAI. Retrying in %s seconds.", e.__class__.__name__, wait_time)
            logger.warning("Error message: %s", e)
            time.sleep(wait_time)

def lambda_handler(event, context):
    """Function to generate an enhanced response that handles conversation flow

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
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps({"response": response})
            }
        except RateLimitError as e:
            logger.error("Rate limit exceeded while generating the response: %s", e)
            return {
                "statusCode": 429,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Rate limit exceeded. Please try again later."})
            }
    except Exception as e:
        logger.error("An error occurred while generating the response: %s", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }
