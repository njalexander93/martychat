"""Model Loader for the Marty chatbot.

This module contains the functions to load the Marty chatbot model and Pinecone index. The model loader initializes the
OpenAI API credentials and the Pinecone index instance to interact with the chatbot model.
"""

__author__ = ["Nikolai Alexander", "Doug Alexander"]
__email__ = "njalexander93@gmail.com, dalexander61@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import json
import openai
import boto3
import logging
import datetime
from pinecone import Pinecone
from dataclasses import dataclass

# Check if the log directory exists, if not create it.
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log") # Stored in ../backend/log
os.makedirs(log_dir, exist_ok=True)

# Configure logging to write to a log file
log_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
log_path = os.path.join(log_dir, f"model_loader-{log_timestamp}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()]
)

@dataclass
class ModelConfig:
    """Data class to store the model configuration for the Marty chatbot.

    Attributes:
        openai_model (str): The OpenAI model to use for the chatbot.
        openai_embedding_model (str): The OpenAI model to use for text embedding.
        temperature (float): The deterministic/randomness of the model.
    """
    openai_model: str
    openai_embedding_model: str
    temperature: float

    @classmethod
    def from_defaults(cls) -> 'ModelConfig':
        """Data class to store the model configuration for the Marty chatbot.

        Returns the configuration to access the OpenAI model. Contains the model name and other metadata to access the model.

        Returns:
            dict: The configuration for the Marty chatbot model.
        """
        return cls(
            openai_model="gpt-4", # Set the OpenAI model to use.
            openai_embedding_model="text-embedding-3-small", # Embedding model for vector search
            temperature=0.7 # Set the deterministic/randomness of the model. Higher the value, the more random the output.
        )

@dataclass
class ApiConfig:
    """Data class to store the API configuration for the OpenAI and Pinecone APIs.

    Returns the configuration to access the OpenAI and Pinecone APIs. Contains the API Keys and other metadata to access

    Attributes:
        openai_api_key (str): The API Key for the OpenAI API.
        openai_org_id (str): The Organization ID for the OpenAI API.
        pinecone_api_key (str): The API Key for the Pinecone API.
        pinecone_env (str): The environment for the Pinecone API.
        pinecone_index_name (str): The name of the Pinecone index.
    """
    openai_api_key: str
    openai_org_id: str
    pinecone_api_key: str
    pinecone_env: str
    pinecone_index_name: str

    @classmethod
    def from_aws(cls) -> 'ApiConfig':
        """Create an instance of ApiConfig from AWS Secrets Manager and AWS Systems Manager Parameter Store.

        Returns:
            ApiConfig: An instance of ApiConfig with values from AWS Systems Manager Parameter Store.
        """
        session = boto3.session.Session()
        secrets_manager = session.client("secretsmanager") # Client for AWS Secrets Manager
        ssm = session.client("ssm") # Client for AWS Systems Manager Parameter Store

        # Get API Keys and Organization ID from AWS Secrets Manager
        logging.info("Getting API keys from AWS Secrets Manager.")
        try:
            secret_id = ssm.get_parameter(Name="/martychat/secrets/api_keys")["Parameter"]["Value"]
            openai_api_key = secrets_manager.get_secret_value(SecretId=secret_id)
            secrets = json.loads(openai_api_key["SecretString"])

            openai_api_key = secrets["openai_api_key"]
            openai_org_id = secrets["openai_org_id"]
            pinecone_api_key = secrets["pinecone_api_key"]
            logging.info("API keys retrieved successfully!")
        except Exception as e:
            logging.exception("Error getting secrets from AWS Secrets Manager.")
            raise RuntimeError("Error getting secrets from AWS Secrets Manager.") from e

        # Get the Pinecone Env and Index Name from AWS Systems Manager Parameter Store
        logging.info("Getting Pinecone environment and index name from AWS Systems Manager Parameter Store.")
        try:
            pinecone_env = ssm.get_parameter(Name="/marty/pinecone/env")["Parameter"]["Value"]
            pinecone_index_name = ssm.get_parameter(Name="/marty/pinecone/index")["Parameter"]["Value"]
            logging.info("Pinecone environment and index name retrieved successfully!")
        except Exception as e:
            logging.exception("Error getting parameters from AWS Systems Manager Parameter Store.")
            raise RuntimeError("Error getting parameters from AWS Systems Manager Parameter Store.") from e

        return cls(
            openai_api_key=openai_api_key,
            openai_org_id=openai_org_id,
            pinecone_api_key=pinecone_api_key,
            pinecone_env=pinecone_env,
            pinecone_index_name=pinecone_index_name
        )

def set_openai_client():
    """Initializes the OpenAI API client globally.

    Initializes the OpenAI API client globally with the API Key and Organization ID from the API configuration stored in
    AWS Secrets Manager.

    Raises:
        ValueError: If the OpenAI API Key or Organization ID is missing.
    """
    # Load the API configurations
    api_config = ApiConfig.from_aws()

    # Check if the OpenAI API Key and Organization ID are set in the api_config
    if not api_config.openai_api_key:
        logging.error("OpenAI API Key is missing.")
        raise ValueError("OpenAI API Key is missing.")
    if not api_config.openai_org_id:
        logging.error("OpenAI Organization ID is missing.")
        raise ValueError("OpenAI Organization ID is missing.")

    # Create an OpenAI API client
    logging.info("Initializing OpenAI API client.")
    try:
        openai.api_key = api_config.openai_api_key
        openai.organization = api_config.openai_org_id
        logging.info("OpenAI API client initialized successfully!")
    except Exception as e:
        logging.exception("Error initializing OpenAI API client.")
        raise RuntimeError("Error initializing OpenAI API client.") from e

def get_pinecone_index() -> Pinecone.Index:
    """Returns a Pinecone Index instance with the configured API Key and Index Name set.

    Returns:
        Pinecone.Index: A Pinecone Index instance.
    Raises:
        ValueError: If the Pinecone API Key or Index Name is missing.
    """
    # Load the API configurations
    api_config = ApiConfig.from_aws()

    # Check if the Pinecone API Key and Index Name are set in the api_config
    if not api_config.pinecone_api_key:
        logging.error("Pinecone API Key is missing.")
        raise ValueError("Pinecone API Key is missing.")
    if not api_config.pinecone_index_name:
        logging.error("Pinecone Index Name is missing.")
        raise ValueError("Pinecone Index Name is missing.")

    # Create a Pinecone Index instance
    logging.info("Initializing Pinecone Index.")
    try:
        pinecone = Pinecone(api_key=api_config.pinecone_api_key)
        pinecone_index = pinecone.Index(api_config.pinecone_index_name)
        logging.info("Pinecone Index initialized successfully!")
    except Exception as e:
        logging.exception("Error initializing Pinecone Index.")
        raise RuntimeError("Error initializing Pinecone Index.") from e

    return pinecone_index

def load_model() -> dict:
    """Loads the model configuration for the Marty chatbot.

    Loads the model configuration for the Marty chatbot, including the OpenAI model and Pinecone index.

    Returns:
        dict: A dictionary containing the OpenAI model, Pinecone index, and other metadata.
    Raises:
        ValueError: If the OpenAI API Key or Organization ID is missing.
        ValueError: If the Pinecone API Key or Index Name is missing.
    """
    # Load the API and model configurations
    model_config = ModelConfig.from_defaults()

    logging.info("Setting up MartyChat client.")
    return {
        "openai_model": model_config.openai_model,
        "openai_embedding_model": model_config.openai_embedding_model,
        "pinecone_index": get_pinecone_index(),
        "temperature": model_config.temperature
    }
