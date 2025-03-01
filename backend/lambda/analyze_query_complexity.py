"""Lambda function for analyzing the k-complexity of a message.

The Lambda function receives a message from the chat interface and calculates the k-complexity of the message. The k-complexity is a measure of the
complexity of a message based on the number of unique words in the message. The function returns the k-complexity of the message.
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

def lambda_handler(event, context):
    """Lambda handler for analyzing the k-complexity of a message.

    This function receives a message from the chat interface and calculates the k-complexity of the message.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.
    Returns:
        dict: The response data to return from the Lambda function.
    """
    try:
        logger.info(f"Received event: {event}")
        body = json.loads(event["body"])
        message = body.get("message")
        if not message:
            raise ValueError("Message is required in the request body")
        logger.info(f"Analyzing message complexity: {message}")

        word_count = len(message.split())
        contains_comparison = any(word in message.lower() for word in ['compare', 'contrast', 'difference', 'relationship', 'versus', 'impact'])
        contains_theory = any(word in message.lower() for word in ['theory', 'concept', 'framework', 'approach', 'model'])
        contains_specific = any(word in message.lower() for word in ['specific', 'particular', 'exactly', 'precisely'])
        logger.info(f"Word count: {word_count}")

        # Determine base k value
        if contains_specific:
            logger.info("Specific query detected")
            base_k = 3 # More focused retrieval for specific queries
        elif contains_comparison or contains_theory:
            logger.info("Comparison or theory query detected")
            base_k = 7 # Broader retrieval for comparison or theory queries
        else:
            logger.info("General query detected")
            base_k = 5 # Default k value for general queries

        # Adjust k value based on word count
        if word_count > 15:
            base_k += 2

        logger.info(f"Returning base k-value: {base_k}")
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"k": base_k})
        }
    except Exception as e:
        logger.error(f"An error occurred while analyzing message complexity: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }
