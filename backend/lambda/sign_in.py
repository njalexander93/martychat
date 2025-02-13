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

def get_client_id() -> str:
    """Retrieve the AWS Cognito App Client ID from AWS Systems Manager Parameter Store.

    Returns:
        str: The AWS Cognito App Client ID.
    """
    session = boto3.session.Session()
    ssm = session.client("ssm")  # Client for AWS Systems Manager Parameter Store

    cognito_client_param = os.getenv("COGNITO_CLIENT_PARAM")
    if not cognito_client_param:
        logger.error("COGNITO_CLIENT_PARAM environment variable is not set.")
        raise RuntimeError("COGNITO_CLIENT_PARAM environment variable is not set.")

    try:
        cognito_client_id = ssm.get_parameter(Name=cognito_client_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("Error getting Cognito Client ID from AWS Systems Manager Parameter Store.")
        raise RuntimeError("Error getting Cognito Client ID from AWS Systems Manager Parameter Store.") from e

    return cognito_client_id


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

        # Get the Cognito user pool ID from AWS Systems Manager Parameter Store
        user_pool_id = get_user_pool_id()
        client_id = get_client_id()

        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("AWS_REGION", "us-east-1"))

        try:
            response = cognito_client.initiate_auth(
                UserPoolId=user_pool_id,
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
                ClientId=client_id
            )
        except cognito_client.exceptions.NotAuthorizedException:
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
