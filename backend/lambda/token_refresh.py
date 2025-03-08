"""Lambda function for refreshing authentication tokens.

This Lambda function refreshes the authentication tokens using the refresh token from AWS Cognito. It returns
new access and ID tokens.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "2025-02-28"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import base64
import hashlib
import hmac
import json
import logging
import os

import boto3
import botocore.exceptions

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


def get_user_pool_id() -> str:
    """Retrieve the AWS Cognito User Pool ID from AWS Systems Manager Parameter Store.

    Returns:
        str: The AWS Cognito User Pool ID.
    """
    session = boto3.session.Session()
    ssm = session.client("ssm")  # Client for AWS Systems Manager Parameter Store

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
    secrets_manager = session.client("secretsmanager")  # Client for AWS Secrets Manager
    ssm = session.client("ssm")  # Client for AWS Systems Manager Parameter Store

    # Validate that the cognito client secret is set in the environment variables
    infra_secret_param = os.getenv("INFRA_SECRETS_PARAM")
    if not infra_secret_param:
        logger.error("INFRA_SECRETS_PARAM environment variable is not set.")
        raise RuntimeError("INFRA_SECRETS_PARAM environment variable is not set.")

    # Get the Cognito client secret from AWS Secrets Manager
    try:
        secret_id = ssm.get_parameter(Name=infra_secret_param, WithDecryption=True)["Parameter"]["Value"]
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

    return {"cognito_client_id": cognito_client_id, "cognito_client_secret": cognito_client_secret}


def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Generate the secret hash for the AWS Cognito authentication request.

    Args:
        username (str): The username of the user signing in.
        client_id (str): The client ID of the AWS Cognito app.
        client_secret (str): The client secret of the AWS Cognito app.

    Returns:
        str: The secret hash for the authentication request.
    """
    logger.info("Generating secret hash for %s with client ID %s", username, client_id)
    message = username + client_id

    dig = hmac.new(key=client_secret.encode("utf-8"), msg=message.encode("utf-8"), digestmod=hashlib.sha256).digest()

    return base64.b64encode(dig).decode()


def lambda_handler(event: dict, context: object) -> dict:
    """Lambda handler for refreshing authentication tokens.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response data containing new authentication tokens.
    """
    try:
        logger.info("Received token refresh request")
        logger.info("Event: %s", json.dumps(event))

        # Retrieve the request body from the event data
        body = json.loads(event["body"])
        refresh_token = body.get("refreshToken")
        user_id = body.get("userId")

        if not refresh_token:
            logger.error("Refresh token is required.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Refresh token is required."}),
            }
        if not user_id:
            logger.error("User ID is required.")
            return {"statusCode": 400, "headers": CORS_HEADERS, "body": json.dumps({"error": "User ID is required."})}

        # Get the Cognito user pool ID, client ID, and client secret
        cognito_client_metadata = get_client_metadata()
        user_pool_id = get_user_pool_id()  # We still need this for logging/verification
        client_id = cognito_client_metadata["cognito_client_id"]
        client_secret = cognito_client_metadata["cognito_client_secret"]

        # Generate the secret hash for the authentication request
        secret_hash = get_secret_hash(user_id, client_id, client_secret)

        # Create a client for the AWS Cognito service
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))

        # Log additional details about the user pool and client
        try:
            user_pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            logger.info(
                "User Pool Refresh Token Validity: %s days",
                user_pool_response["UserPool"]["Policies"]["PasswordPolicy"].get("RefreshTokenValidity", "Not Found"),
            )
        except Exception as pool_error:
            logger.warning("Could not retrieve user pool details: %s", pool_error)

        try:
            logger.info("Initiating token refresh")
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token, "SECRET_HASH": secret_hash},
            )
        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "NotAuthorizedException":
                logger.exception("NotAuthorizedException has appeared: %s", e)
                return {
                    "statusCode": 401,
                    "headers": CORS_HEADERS,
                    # "body": json.dumps({"error": f"Refresh token is invalid or expired. TOKEN {refresh_token}"})
                    "body": json.dumps({"error": f"NotAuthorizedException has appeared: {e!s}"}),
                }

            logger.exception("Error refreshing tokens.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error refreshing tokens: {e!s}"}),
            }

        # Add expiration times to the authentication result
        authentication_result = response["AuthenticationResult"]
        expires_in = authentication_result.get("ExpiresIn", 3600)  # Default to 1 hour if not specified
        authentication_result["idTokenExpires"] = expires_in
        authentication_result["accessTokenExpires"] = expires_in

        # Get refresh token expiration from user pool
        try:
            user_pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            refresh_token_validity = user_pool_response["UserPool"]["Policies"]["PasswordPolicy"].get(
                "RefreshTokenValidity", 30
            )
            authentication_result["refreshTokenExpires"] = refresh_token_validity * 24 * 60 * 60
        except Exception as e:
            logger.warning("Could not get refresh token validity: %s", e)
            authentication_result["refreshTokenExpires"] = 30 * 24 * 60 * 60  # Default to 30 days

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {"message": "Tokens refreshed successfully.", "authenticationResult": authentication_result}
            ),
        }
    except Exception as e:
        logger.exception("Error refreshing tokens.")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error refreshing tokens: {e!s}"}),
        }
