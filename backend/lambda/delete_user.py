"""Lambda function for deleting a user from AWS Cognito and DynamoDB.

This Lambda function processes a request to delete a user from the AWS Cognito user pool and the DynamoDB users table.
It verifies the request and properly removes the user data from both services.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
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


def delete_user_from_cognito(username: str) -> bool:
    """Delete a user from the AWS Cognito user pool.

    Args:
        username (str): The username of the user to delete.

    Returns:
        bool: True if the user was successfully deleted, False otherwise.

    Raises:
        RuntimeError: An error occurred deleting the user from AWS Cognito.
    """
    cognito_user_pool_id = get_user_pool_id()
    cognito_client_metadata = get_client_metadata()

    client_id = cognito_client_metadata["cognito_client_id"]
    client_secret = cognito_client_metadata["cognito_client_secret"]
    secret_hash = get_secret_hash(username, client_id, client_secret)

    # Create a client for the AWS Cognito service
    cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))

    try:
        cognito_client.admin_delete_user(
            UserPoolId=cognito_user_pool_id,
            Username=username,
            ClientId=client_id,
            SecretHash=secret_hash,
        )
        logger.info(f"User {username} deleted from AWS Cognito.")
        return True
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "UserNotFoundException":
            logger.warning("User not found in AWS Cognito.")
            return False

        logger.exception("Error deleting user from AWS Cognito.")
        raise RuntimeError("Error deleting user from AWS Cognito.") from e
    except Exception as e:
        logger.exception(f"Error deleting user {username} from AWS Cognito.")
        raise RuntimeError(f"Error deleting user {username} from AWS Cognito.") from e


def delete_user_from_dynamodb(user_id: str) -> bool:
    """Delete a user from the DynamoDB users table.

    Args:
        user_id (str): The user ID of the user to delete.

    Returns:
        bool: True if the user was successfully deleted, False otherwise.
    """
    ssm = boto3.client("ssm")  # Client for AWS Secrets Manager

    # Initialize the DynamoDB client
    try:
        dynamodb_user_table_param = os.getenv("DYNAMODB_USER_TABLE_PARAM")
        if not dynamodb_user_table_param:
            logger.error("DYNAMODB_TABLE_NAME environment variable is not set.")
            raise RuntimeError("DYNAMODB_TABLE_NAME environment variable is not set.")

        table_name = ssm.get_parameter(Name=dynamodb_user_table_param)["Parameter"]["Value"]
        dynamodb_client = boto3.resource("dynamodb", region_name=os.getenv("REGION_NAME", "us-east-1"))
        table = dynamodb_client.Table(table_name)
    except Exception as e:
        logger.exception("Failed to initialize DynamoDB client.")
        raise RuntimeError(f"Failed to initialize DynamoDB client: {e}") from e

    try:
        # Check if the user exists in DynamoDB
        response = table.get_item(Key={"user_id": user_id})
        if "Item" not in response:
            logger.warning(f"User with ID {user_id} not found in DynamoDB.")
            return False

        # Delete the user from DynamoDB
        table.delete_item(Key={"user_id": user_id})
        logger.info(f"User with ID {user_id} deleted from DynamoDB successfully.")
        return True
    except Exception as e:
        logger.exception(f"Error deleting user from DynamoDB: {e}")
        raise RuntimeError(f"Error deleting user from DynamoDB: {e}") from e


def get_user_id(username: str) -> str:
    """Retrieve the user ID from the Cognito user pool using the user's username.

    Args:
        username (str): The username of the user to retrieve the ID for.

    Returns:
        str: The user ID of the user.

    Raises:
        RuntimeError: An error occurred getting the user ID from AWS Cognito.
        RuntimeError: The user was not found in AWS Cognito.
        RuntimeError: An error occurred getting the user ID from AWS Cognito.
    """
    cognito_user_pool_id = get_user_pool_id()
    cognito_client_metadata = get_client_metadata()

    client_id = cognito_client_metadata["cognito_client_id"]
    client_secret = cognito_client_metadata["cognito_client_secret"]
    secret_hash = get_secret_hash(username, client_id, client_secret)

    # Create a client for the AWS Cognito service
    cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))

    try:
        user_info = cognito_client.admin_get_user(
            UserPoolId=cognito_user_pool_id, Username=username, ClientId=client_id, SecretHash=secret_hash
        )

        for attribute in user_info["UserAttributes"]:
            if attribute["Name"] == "sub":
                return attribute["Value"]

        raise RuntimeError(f"User ID not found for user {username}")
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "UserNotFoundException":
            logger.exception(f"User {username} not found in AWS Cognito.")
            raise RuntimeError(f"User {username} not found in AWS Cognito.") from e

        logger.exception("Error deleting user from AWS Cognito.")
        raise RuntimeError("Error deleting user from AWS Cognito.") from e
    except Exception as e:
        logger.exception(f"Error getting user ID for {username}: {e}")
        raise RuntimeError(f"Error getting user ID for {username}: {e}") from e


def lambda_handler(event: dict, context: object) -> dict:
    """Lambda function handler for deleting a user from AWS Cognito and DynamoDB.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response data to return to the client.
    """
    try:
        body = json.loads(event["body"])
        username = body.get("username")

        if not username:
            logger.error("Invalid request body. Missing 'username' field.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Invalid request body."}),
            }

        # Get the user ID from AWS Cognito
        try:
            user_id = get_user_id(username)
        except RuntimeError as e:
            logger.exception(f"Error getting user ID for {username}: {e}")
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Internal Server Error"}),
            }

        # Delete the user from AWS Cognito
        try:
            cognito_result = delete_user_from_cognito(username)
            if not cognito_result:
                logger.error(f"User {username} not found in AWS Cognito.")
                return {
                    "statusCode": 404,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "User not found."}),
                }
        except RuntimeError as e:
            logger.exception(f"Error deleting user {username} from AWS Cognito: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Internal Server Error"}),
            }

        # Delete the user from DynamoDB
        try:
            dynamodb_result = delete_user_from_dynamodb(user_id)
            if not dynamodb_result:
                logger.error(f"User with ID {user_id} not found in DynamoDB.")
                return {
                    "statusCode": 404,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "User not found."}),
                }
        except RuntimeError as e:
            logger.exception(f"Error deleting user from DynamoDB: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Internal Server Error"}),
            }

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "User deleted successfully."}),
        }
    except Exception as e:
        logger.exception(f"Error deleting the user: {e}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Internal Server Error"}),
        }
