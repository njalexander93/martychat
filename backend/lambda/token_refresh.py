"""Lambda function for refreshing authentication tokens.

This Lambda function refreshes the authentication tokens using the refresh token from AWS Cognito. It returns
new access and ID tokens.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import json
import logging
import boto3
import botocore.exceptions
import base64
import hmac
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()] # Only use StreamHandler for CloudWatch
)
logger = logging.getLogger(__name__)

# Set the CORS headers for the response
CORS_HEADERS = {
    "Content-Type": "application/json",
    "X-Custom-Header": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS, GET, POST, PUT, PATCH, DELETE",
    "Access-Control-Allow-Headers": "X-Requested-With, content-type",
    "Access-Control-Allow-Credentials": "true"  # Required for credentials-based requests
}

def get_user_pool_id() -> str:
    """Retrieve the AWS Cognito User Pool ID from AWS Systems Manager Parameter Store.

    Returns:
        str: The AWS Cognito User Pool ID.
    """
    session = boto3.session.Session()
    ssm = session.client("ssm") # Client for AWS Systems Manager Parameter Store

    cognito_user_param = os.getenv("COGNITO_USER_PARAM")
    if not cognito_user_param:
        logger.error("COGNITO_USER_PARAM environment variable is not set.")
        raise RuntimeError("COGNITO_USER_PARAM environment variable is not set.")

    try:
        cognito_user_pool_id = ssm.get_parameter(Name=cognito_user_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("Error getting Cognito ID from AWS Systems Manager Parameter Store.")
        raise RuntimeError("Error getting Cognito ID from AWS Systems Manager Parameter Store.") from e

    return cognito_user_pool_id

def get_client_metadata() -> dict:
    """Retrieve the AWS Cognito App Client ID from AWS Systems Manager Parameter Store.

    Returns:
        dict: The AWS Cognito App Client ID and Client Secret.
    """
    session = boto3.session.Session()
    secrets_manager = session.client("secretsmanager") # Client for AWS Secrets Manager
    ssm = session.client("ssm") # Client for AWS Systems Manager Parameter Store

    # Validate that the cognito client secret is set in the environment variables
    infra_secret_param = os.getenv("INFRA_SECRETS_PARAM")
    if not infra_secret_param:
        logger.error("INFRA_SECRETS_PARAM environment variable is not set.")
        raise RuntimeError("INFRA_SECRETS_PARAM environment variable is not set.")

    # Get the Cognito client secret from AWS Secrets Manager
    try:
        secret_id = ssm.get_parameter(Name=os.getenv("INFRA_SECRETS_PARAM"), WithDecryption=True)["Parameter"]["Value"]
        secret_key = secrets_manager.get_secret_value(SecretId=secret_id)
        secrets = json.loads(secret_key["SecretString"])

        cognito_client_secret = secrets["cognito_client_secret"]
        logging.info("Cognito client secret retrieved successfully!")
    except Exception as e:
        logging.exception("Error getting secrets from AWS Secrets Manager.")
        raise RuntimeError("Error getting secrets from AWS Secrets Manager.") from e

    # Validate that the cognito client secret is set in the environment variables
    cognito_client_param = os.getenv("COGNITO_CLIENT_PARAM")
    if not cognito_client_param:
        logger.error("COGNITO_CLIENT_PARAM environment variable is not set.")
        raise RuntimeError("COGNITO_CLIENT_PARAM environment variable is not set.")

    # Get the Cognito client ID from AWS Systems Manager Parameter Store
    try:
        cognito_client_id = ssm.get_parameter(Name=cognito_client_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("Error getting Cognito Client ID from AWS Systems Manager Parameter Store.")
        raise RuntimeError("Error getting Cognito Client ID from AWS Systems Manager Parameter Store.") from e

    return {
        "cognito_client_id": cognito_client_id,
        "cognito_client_secret": cognito_client_secret
    }

def lambda_handler(event, context):
    """Lambda handler for refreshing authentication tokens.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.
    Returns:
        dict: The response data containing new authentication tokens.
    """
    try:
        logger.info("Received token refresh request")
        logger.info(f"Event: {json.dumps(event)}")

        # Retrieve the request body from the event data
        body = json.loads(event["body"])
        refresh_token = body.get("refreshToken")

        if not refresh_token:
            logger.error("Refresh token is required.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Refresh token is required."})
            }

        # Get the Cognito client metadata
        cognito_client_metadata = get_client_metadata()
        user_pool_id = get_user_pool_id()
        client_id = cognito_client_metadata["cognito_client_id"]

        # Create a client for the AWS Cognito service
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("AWS_REGION", "us-east-1"))

        try:
            logger.info("Initiating token refresh")
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token
                }
            )
        except cognito_client.exceptions.NotAuthorizedException:
            logger.error("Refresh token is invalid or expired.")
            return {
                "statusCode": 401,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Refresh token is invalid or expired."})
            }
        except botocore.exceptions.ClientError as e:
            logger.exception("Error refreshing tokens.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error refreshing tokens: {str(e)}"})
            }

        # Add expiration times to the authentication result
        authentication_result = response["AuthenticationResult"]
        expires_in = authentication_result.get("ExpiresIn", 3600)  # Default to 1 hour if not specified
        authentication_result["idTokenExpires"] = expires_in
        authentication_result["accessTokenExpires"] = expires_in

        # Get refresh token expiration from user pool
        try:
            user_pool_response = cognito_client.describe_user_pool(
                UserPoolId=user_pool_id
            )
            refresh_token_validity = user_pool_response["UserPool"]["Policies"]["PasswordPolicy"].get("RefreshTokenValidity", 30)
            authentication_result["refreshTokenExpires"] = refresh_token_validity * 24 * 60 * 60
        except Exception as e:
            logger.warning(f"Could not get refresh token validity: {str(e)}")
            authentication_result["refreshTokenExpires"] = 30 * 24 * 60 * 60  # Default to 30 days

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "message": "Tokens refreshed successfully.",
                "authenticationResult": authentication_result
            })
        }
    except Exception as e:
        logger.exception("Error refreshing tokens.")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error refreshing tokens: {str(e)}"})
        }
