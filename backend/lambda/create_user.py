"""Lambda function adding a new user to AWS Congito.

This Lambda function processes a request from the sign up page to create a new user in AWS Cognito. The function
validates the request and creates a new user in the Cognito user pool.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "2025-02-28"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import json
import datetime
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
    logger.info(f"Generating secret hash for {username} with client ID {client_id}")
    message = username + client_id

    dig = hmac.new(
        key=client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    return base64.b64encode(dig).decode()

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

    # Get the Cognito user pool ID, client ID, and client secret
    cognito_client_metadata = get_client_metadata()
    user_pool_id = get_user_pool_id()  # We still need this for logging/verification
    client_id = cognito_client_metadata["cognito_client_id"]
    client_secret = cognito_client_metadata["cognito_client_secret"]

    # Initialize the Cognito client
    try:
        cognito_client = boto3.client("cognito-idp", region_name=os.getenv("REGION_NAME", "us-east-1"))
    except Exception as e:
        logger.exception("Failed to initialize Cognito client.")
        raise RuntimeError(f"Failed to initialize Cognito client: {e}") from e

    try:
        # Create the new user in the Cognito user pool
        temp_password = f"Temp1{os.urandom(8).hex()}"
        secret_hash = get_secret_hash(email, client_id, client_secret)

        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=temp_password,
            UserAttributes=[{"Name": "email", "Value": email}],
            MessageAction="SUPPRESS",  # Prevents Cognito from sending an email to the user
        )

        # Initiate authentication with the temporary password
        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": temp_password,
                "SECRET_HASH": secret_hash
            }
        )

        # Set the user's password to a permanent value
        try:
            new_secret_hash = get_secret_hash(email, client_id, client_secret)
            cognito_client.admin_respond_to_auth_challenge(
                UserPoolId=user_pool_id,
                ClientId=client_id,
                ChallengeName=auth_response['ChallengeName'],
                ChallengeResponses={
                    'USERNAME': email,
                    'NEW_PASSWORD': password,
                    'SECRET_HASH': new_secret_hash
                },
                Session=auth_response['Session']
            )
        except cognito_client.exceptions.InvalidPasswordException as e:
            # If setting the password fails, delete the user and raise the exception
            cognito_client.admin_delete_user(UserPoolId=user_pool_id, Username=email)
            if "Password has previously been used" in str(e):
                logger.error("This password has been previously used for this account.")
                raise RuntimeError("This password has been previously used for this account.")
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
