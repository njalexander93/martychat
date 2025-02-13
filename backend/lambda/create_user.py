"""Lambda function adding a new user to AWS Congito.

This Lambda function processes a request from the sign up page to create a new user in AWS Cognito. The function
validates the request and creates a new user in the Cognito user pool.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import json
import datetime
import logging
import boto3
import botocore.exceptions

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

def create_cognito_user(signup_parameters: dict) -> str:
    """Create a new user in the AWS Cognito user pool.

    Args:
        signup_parameters (dict): A dictionary containing the user information from the sign up form.
    Returns:
        str: The unique user ID (sub) from Cognito.
    Raises:
        RuntimeError: An error occurred initializing the Cognito client.
        RuntimeError: An error occurred creating the user in Cognito.
        RuntimeError: An error occurred getting the user ID from the Cognito response.
    """
    # Get the user information from the sign up form.
    email = signup_parameters["email"]
    password = signup_parameters["password"]

    # Get the Cognito user pool ID from AWS Systems Manager Parameter Store.
    user_pool_id = get_user_pool_id()

    # Initialize the Cognito client
    try:
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))
    except Exception as e:
        logger.exception("Failed to initialize Cognito client.")
        raise RuntimeError(f"Failed to initialize Cognito client: {e}") from e

    try:
        # Create the new user in the Cognito user pool
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=password,
            UserAttributes=[{"Name": "email", "Value": email}],
            MessageAction="SUPPRESS",  # Prevents Cognito from sending an email to the user
        )

        # Set the user's password to a permanent value
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
    except cognito_client.exceptions.UsernameExistsException:
        logger.error("User already exists.")
        raise RuntimeError("User already exists.")
    except botocore.exceptions.ClientError as e:
        logger.exception("Error creating user in Cognito.")
        raise RuntimeError(f"AWS Cognito error: {e.response['Error']['Message']}") from e

    try:
        # Get the unique user ID (sub) from the Cognito user attributes.
        user_id = next(attr["Value"] for attr in response["User"]["Attributes"] if attr["Name"] == "sub")
    except StopIteration:
        logger.error("Error getting user ID from Cognito response.")
        raise RuntimeError("Error getting user ID from Cognito response.")

    return user_id

def add_user_to_dynamodb(signup_parameters: dict) -> None:
    """Add the user profile data to the DynamoDB table.

    Args:
        signup_parameters (dict): A dictionary containing the user information from the sign up form.
    Raises:
        RuntimeError: An error occurred initializing the DynamoDB client.
        RuntimeError: An error occurred adding the user to the DynamoDB table.
    """
    # Initialize the DynamoDB client
    try:
        dynamodb_client = boto3.resource("dynamodb", region_name=os.getenv("REGION_NAME", "us-east-1"))
        table = dynamodb_client.Table("martychat_users-development")
    except Exception as e:
        logger.exception("Failed to initialize DynamoDB client.")
        raise RuntimeError(f"Failed to initialize DynamoDB client: {e}") from e

    # Add the user profile data to the DynamoDB table
    try:
        table.put_item(
            Item={
                "user_id": signup_parameters["user_id"],
                "email": signup_parameters["email"],
                "first_name": signup_parameters["first_name"],
                "last_name": signup_parameters["last_name"],
                "organization": signup_parameters.get("organization", "N/A"),
                "created_at": signup_parameters["created_at"],
                "last_login": signup_parameters["last_login"]
            }
        )
    except Exception as e:
        logger.exception("Error adding user to DynamoDB.")
        raise RuntimeError(f"Error adding user to DynamoDB: {str(e)}") from e

    return

def lambda_handler(event, context):
    """Lambda handler for adding a new user to AWS Cognito.

    This function processes a request from the sign up page to create a new user in AWS Cognito. The function

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.
    Returns:
        dict: The response data to return from the Lambda function.
    """

    try:
        # Parse the request body to get the user information from the sign up form
        body = json.loads(event["body"])
        signup_parameters = {
            "email": body.get("email", "").strip(),
            "password": body.get("password", "").strip(),
            "first_name": body.get("firstName", "").strip(),
            "last_name": body.get("lastName", "").strip(),
            "organization": body.get("organization", "").strip() or "N/A",
            "created_at": datetime.datetime.now().isoformat(),
            "last_login": datetime.datetime.now().isoformat()
        }

        # Validate that all required fields are present
        required_fields = ["email", "password", "first_name", "last_name"]
        if not all(signup_parameters[field] for field in required_fields):
            logger.error("Missing required fields.")
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Missing required fields."})
            }

        # Create the new user in the Cognito user pool
        try:
            signup_parameters["user_id"] = create_cognito_user(signup_parameters)
        except RuntimeError as e:
            if "User already exists." in str(e):
                logger.error("User already exists.")
                return {
                    "statusCode": 400,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"error": "User already exists."})
                }
            logger.exception("Error creating user in Cognito.")
            return {
                "statusCode": 500,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": str(e)})
            }

        # Add the user profile data to the DynamoDB table
        add_user_to_dynamodb(signup_parameters)

        return {
            "statusCode": 201,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "User created successfully!", "user": signup_parameters["user_id"]})
        }
    except Exception as e:
        logger.exception("Error creating user.")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})\
        }
