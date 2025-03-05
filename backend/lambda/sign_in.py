"""Lambda function for signing in a user.

This Lambda function signs in a user by validating the user's credentials against the AWS Cognito user pool. It returns
an authentication result that includes a id token, access token, and refresh token.
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
    logger.info(f"Generating secret hash for {username} with client ID {client_id}")
    message = username + client_id

    dig = hmac.new(key=client_secret.encode("utf-8"), msg=message.encode("utf-8"), digestmod=hashlib.sha256).digest()

    return base64.b64encode(dig).decode()


def get_user_id(cognito_client: boto3.client, access_token: str) -> str:
    """Get the userID from the AWS Cognito user pool using the access token.

    Args:
        cognito_client (boto3.client): The AWS Cognito client.
        access_token (str): The access token for the user.

    Returns:
        str: The user ID of the authenticated user.
    """
    try:
        response = cognito_client.get_user(AccessToken=access_token)

        user_id = None
        for attribute in response["UserAttributes"]:
            if attribute["Name"] == "sub":
                user_id = attribute["Value"]

        if not user_id:
            logger.error("User ID not found in Cognito response.")
            raise RuntimeError("User ID not found in Cognito response.")

        return user_id
    except Exception as e:
        logger.exception("Error getting user ID from AWS Cognito.")
        raise RuntimeError("Error getting user ID from AWS Cognito.") from e


def lambda_handler(event: dict, context: object) -> dict:
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
        logger.info("Event: %s", json.dumps(event))

        # Retrieve the request body from the event data
        body = json.loads(event["body"])
        email = body["email"]
        password = body["password"]

        if not email or not password:
            logger.error("Email and password are required.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Email and password are required."}),
            }

        # Get the Cognito user pool ID, client ID, and client secret
        cognito_client_metadata = get_client_metadata()
        user_pool_id = get_user_pool_id()  # We still need this for logging/verification
        client_id = cognito_client_metadata["cognito_client_id"]
        client_secret = cognito_client_metadata["cognito_client_secret"]

        # Generate the secret hash for the authentication request
        secret_hash = get_secret_hash(email, client_id, client_secret)

        # Create a client for the AWS Cognito service
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))

        try:
            logger.info("Initiating Cognito authentication")
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password, "SECRET_HASH": secret_hash},
            )
        except cognito_client.exceptions.NotAuthorizedException as e:
            error_msg = str(e)
            logger.error("NotAuthorizedException details: %s", error_msg)
            logger.error("Client ID used: %s", client_id)

            # Check if there are any specific error indicators
            if "password" in error_msg.lower():
                logger.error("Error appears to be password-related")
            elif "user" in error_msg.lower():
                logger.error("Error appears to be username-related")

            logger.error("Incorrect username or password.")
            return {
                "statusCode": 401,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Incorrect username or password."}),
            }
        except cognito_client.exceptions.UserNotFoundException:
            logger.error("User does not exist.")
            return {"statusCode": 404, "headers": CORS_HEADERS, "body": json.dumps({"error": "User does not exist."})}
        except botocore.exceptions.ClientError as e:
            logger.exception("Error authenticating user.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error authenticating user: {e!s}"}),
            }

        # Get the user ID from the access token.
        try:
            access_token = response["AuthenticationResult"]["AccessToken"]
            user_id = get_user_id(cognito_client, access_token)
        except Exception as e:
            logger.exception("Error getting user ID from AWS Cognito.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": f"Error getting user ID from AWS Cognito: {e!s}"}),
            }

        logger.info(f"AuthenticationResult: {response['AuthenticationResult']}")

        # Add the user ID to the authentication result
        authentication_result = response["AuthenticationResult"]
        authentication_result["UserId"] = user_id

        # Get the expiration times for each token
        authentication_result["IdTokenExpires"] = response["AuthenticationResult"].get("ExpiresIn")
        authentication_result["AccessTokenExpires"] = response["AuthenticationResult"].get("ExpiresIn")
        try:
            user_pool_response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
            refresh_token_validity = user_pool_response["UserPool"]["Policies"]["PasswordPolicy"].get(
                "RefreshTokenValidity", 30
            )
            authentication_result["RefreshTokenExpires"] = refresh_token_validity * 24 * 60 * 60
        except Exception as e:
            logger.warning(f"Could not get refresh token validity: {e!s}")
            # Default to 30 days if we can't get the actual value
            authentication_result["refreshTokenExpires"] = 30 * 24 * 60 * 60

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(
                {"message": "User authenticated successfully.", "authenticationResult": authentication_result}
            ),
        }
    except Exception as e:
        logger.exception("Error signing in user.")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Error signing in user: {e!s}"}),
        }
