"""Lambda function for signing in a user.

This Lambda function signs in a user by validating the user's credentials against the AWS Cognito user pool. It returns
an authentication result that includes a id token, access token, and refresh token.
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
    handlers=[logging.StreamHandler()]  # Only use StreamHandler for CloudWatch
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

def get_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Generate the secret hash for the AWS Cognito authentication request.

    Args:
        username (str): The username of the user signing in.
        client_id (str): The client ID of the AWS Cognito app.
        client_secret (str): The client secret of the AWS Cognito app.
    Returns:
        str: The secret hash for the authentication request.
    """
    message = username + client_id

    dig = hmac.new(
        key=client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    return base64.b64encode(dig).decode()

def lambda_handler(event, context):
    """Lambda handler for signing in a user to AWS Cognito.

    This function processes a request from the sign in page to authenticate a user in the AWS Cognito user pool. The
    function validates the request and returns an authentication result that includes an id token, access token, and
    refresh token.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.
    Returns:
        dict: The response data to return from the Lambda function.
    """
    try:
        logger.info("Received sign-in request")
        logger.info(f"Event: {json.dumps(event)}")

        # Retrieve the request body from the event data
        body = json.loads(event["body"])
        email = body["email"]
        password = body["password"]

        if not email or not password:
            logger.error("Email and password are required.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Email and password are required."})
            }

        # Get the Cognito user pool ID, client ID, and client secret
        cognito_client_metadata = get_client_metadata()
        user_pool_id = get_user_pool_id()  # We still need this for logging/verification
        client_id = cognito_client_metadata["cognito_client_id"]
        client_secret = cognito_client_metadata["cognito_client_secret"]

        # Generate the secret hash for the authentication request
        secret_hash = get_secret_hash(email, client_id, client_secret)

        # Create a client for the AWS Cognito service
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("AWS_REGION", "us-east-1"))

        try:
            logger.info("Initiating Cognito authentication")
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                    "SECRET_HASH": secret_hash
                }
            )

        except cognito_client.exceptions.NotAuthorizedException as e:
            error_msg = str(e)
            logger.error(f"NotAuthorizedException details: {error_msg}")
            logger.error(f"Client ID used: {client_id}")

            # Check if there are any specific error indicators
            if "password" in error_msg.lower():
                logger.error("Error appears to be password-related")
            elif "user" in error_msg.lower():
                logger.error("Error appears to be username-related")

            logger.error("Incorrect username or password.")
            return {
                "statusCode": 401,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Incorrect username or password."})
            }
        except cognito_client.exceptions.UserNotFoundException:
            logger.error("User does not exist.")
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "User does not exist."})
            }
        except botocore.exceptions.ClientError as e:
            logger.exception("Error authenticating user.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error authenticating user: {str(e)}"})
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "message": "User authenticated successfully.",
                "authenticationResult": response["AuthenticationResult"]
            })
        }
    except Exception as e:
        logger.exception("Error signing in user.")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error signing in user: {str(e)}"})
        }
