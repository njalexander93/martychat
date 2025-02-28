"""Lambda function for enhanced document retrieval with deduplication and improved citation formatting.

The Lambda function receives a message from the chat interface and calculates the k-complexity of the message. The k-complexity is a measure of the
complexity of a message based on the number of unique words in the message. The function returns the k-complexity of the message.
"""

__author__ = ["Nikolai Alexander", "Doug Alexander"]
__email__ = "njalexander93@gmail.com, dalexander61@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
import json
import logging
import string
import time
from functools import wraps
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from pinecone import Pinecone
from requests.exceptions import SSLError, ConnectionError, Timeout
import boto3
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

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

OPENAI_EMBEDDING_MODEL = 'text-embedding-3-small'

STOP_WORDS = set(stopwords.words('english'))
PUNCTUATION_TRANSLATOR = str.maketrans('', '', string.punctuation)

# Define domain-specific terms and their expansions
PSYCHOLOGY_TERMS = {
    'psychology': ['psychological', 'theory', 'framework', 'research', 'clinical'],
    'cognitive': ['cognitive', 'processes', 'thinking'],
    'behavior': ['behavioral', 'patterns', 'response'],
    'emotion': ['emotional', 'response', 'feeling', 'affect'],
    'mental': ['mental', 'processes', 'cognition'],
    'therapy': ['therapeutic', 'approach', 'treatment'],
    'research': ['research', 'study', 'findings', 'evidence'],
    'theory': ['theoretical', 'framework', 'concept', 'model'],
    'positive': ['positive', 'psychology', 'wellbeing'],
    'learned': ['learning', 'conditioning', 'acquired'],
    'seligman': ['seligman', 'positive', 'psychology', 'learned', 'helplessness', 'optimism'],
    'compare': ['comparison', 'differences', 'similarities', 'relationship', 'between'],
    'performance': ['performance', 'achievement', 'outcome']
}

def retry_operation(max_retries=3):
    """Decorator for retrying an operation.

    This decorator retries an operation up to a maximum number of times with an exponential backoff.

    Args:
        max_retries (int): The maximum number of retries.
        backoff_factor (float): The backoff factor for exponential backoff.
    Returns:
        function: The decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except (APIError, RateLimitError, APIConnectionError) as e:
                    # Retry on OpenAI API errors
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise e

                    wait_time = 2 ** retry_count
                    logger.warning("Hit a %s error while trying to get a response from OpenAI. Retrying in %s seconds.", e.__class__.__name__, wait_time)
                    logger.warning("Error message: %s", e)
                    time.sleep(wait_time)
                except (SSLError, ConnectionError, Timeout) as e:
                    # Retry on Pinecone connection errors
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise e

                    wait_time = 2 ** retry_count
                    logger.warning("Hit a %s error while trying to connect to the Pinecone index. Retrying in %s seconds.", e.__class__.__name__, wait_time)
                    logger.warning("Error message: %s", e)
                    time.sleep(wait_time)
        return wrapper
    return decorator

def get_api_parameters(aws_parameters: str) -> dict:
    """Function for retrieving the OpenAI API key and organization ID from AWS Secrets Manager.

    This function retrieves the OpenAI API key and organization ID from AWS Secrets Manager. The function assumes that the secrets are stored in the

    Args:
        aws_parameters (str): The AWS parameters containing the API secrets and Pinecone environment.
    Returns:
        dict: The OpenAI API key and organization ID.
    """
    session = boto3.session.Session()
    secrets_manager = session.client("secretsmanager")
    ssm = session.client("ssm")

    api_secrets_param = aws_parameters.get("api_secrets_param")
    pinecone_env_param = aws_parameters.get("pinecone_env_param")
    pinecone_index_param = aws_parameters.get("pinecone_index_param")

    if not api_secrets_param:
        raise RuntimeError("api_secrets_param is required in the AWS parameters.")
    if not pinecone_env_param:
        raise RuntimeError("pinecone_env_param is required in the AWS parameters.")
    if not pinecone_index_param:
        raise RuntimeError("pinecone_index_param is required in the AWS parameters.")

    try:
        secret_id = ssm.get_parameter(Name=api_secrets_param, WithDecryption=True)["Parameter"]["Value"]
        secret_key = secrets_manager.get_secret_value(SecretId=secret_id)
        secrets = json.loads(secret_key["SecretString"])

        api_parameters = {
            "openai_api_key": secrets["openai_api_key"],
            "openai_org_id": secrets["openai_org_id"],
            "pinecone_api_key": secrets["pinecone_api_key"]
        }
    except Exception as e:
        logger.exception("An error occurred while retrieving the API secrets: %s", e)
        raise RuntimeError("Failed to retrieve the API secrets.") from e

    try:
        api_parameters["pinecone_env"] = ssm.get_parameter(Name=pinecone_env_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("An error occurred while retrieving the Pinecone environment: %s", e)
        raise RuntimeError("Failed to retrieve the Pinecone environment.") from e
    try:
        api_parameters["pinecone_index"] = ssm.get_parameter(Name=pinecone_index_param, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logger.exception("An error occurred while retrieving the Pinecone index: %s", e)
        raise RuntimeError("Failed to retrieve the Pinecone index.") from e

    return api_parameters

def init_pinecone_index(api_key: str, pinecone_env: str, pinecone_index: str) -> Pinecone.Index:
    """Function for initializing the Pinecone index.

    This function initializes the Pinecone index for document retrieval.

    Args:
        api_key (str): The Pinecone API key.
        pinecone_parameters (dict): The Pinecone parameters containing the environment and index name.
    Returns:
        pinecone.Index: The initialized Pinecone index.
    """
    pc = Pinecone(
        api_key=api_key,
        environment=pinecone_env
    )

    return pc.Index(pinecone_index)

def preprocess_message(message: str) -> str:
    """Function for preprocesssing the message for document retrieval.

    This function enhances query quality through basic text preprocessing and domain-specific augmentation.

    Args:
        message (str): The message to preprocess.
    Returns:
        str: The preprocessed message.
    """

    # Convert the case of the message to lowercase and remove all punctuation
    text = message.lower()
    text = text.translate(PUNCTUATION_TRANSLATOR)

    # Remove stopwords from the message and extend psychology terms by domain-specific keyword association.
    enhanced_words = []
    for word in text.split():
        if word not in STOP_WORDS:
            enhanced_words.append(word)
            enhanced_words.extend(PSYCHOLOGY_TERMS.get(word, []))

    enhanced_message = " ".join(enhanced_words)
    return enhanced_message

@retry_operation(max_retries=3)
def get_embeddings_batch(client: OpenAI, search_queries: list) -> list:
    """Function for getting embeddings for a batch of search queries.

    This function retrieves embeddings for a batch of search queries from the OpenAI API.

    Args:
        client (OpenAI): The OpenAI API client.
        search_queries (list): The list of search queries.
    Returns:
        list: The list of embeddings for the search queries.
    """
    embedding_response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=search_queries
    )
    embeddings = [data.embedding for data in embedding_response.data]

    return embeddings

@retry_operation(max_retries=3)
def query_pinecone_index(pinecone_index: Pinecone.Index, embedding: list, k: int) -> dict:
    """Function for querying the Pinecone index for similar documents.

    This function queries the Pinecone index for similar documents based on the provided embedding.

    Args:
        pinecone_index (Pinecone.Index): The Pinecone index.
        embedding (list): The embedding for the search query.
        k (int): The number of similar documents to retrieve.
    Returns:
        dict: The results of the query.
    """
    results = pinecone_index.query(
        vector=embedding,
        top_k=k,
        include_metadata=True
    )

    return results

def format_citation_date(date_str) -> str:
    """Function for formatting the citation date.

    This function formats the date string in the citation to a more readable format.

    Args:
        date_str (str): The date string to format.
    Returns:
        str: The formatted date string.
    """
    try:
        # Handle the D:YYYYMMDDHHmmSS format
        if date_str.startswith('D:'):
            # Extract just the year portion (first 4 digits after 'D:')
            year = date_str[2:6]
            return year

        # Add additional date format handling if needed
        return date_str
    except Exception:
        return 'n.d.'  # Return "no date" for any unparseable dates

def lambda_handler(event, context):
    """Lambda handler for retrieving similar documents based on a query.

    This function receives a query from the chat interface and retrieves similar documents from the Pinecone index. The function deduplicates the
    retrieved documents and formats the citations for display.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.
    Returns:
        dict: The response data to return from the Lambda function.
    """
    try:
        # Parse the request body for parameters
        body = json.loads(event["body"])
        message = body.get("message")
        k = body.get("k")
        aws_parameters = body.get("aws_parameters")

        # Validate the request parameters
        if not message:
            raise ValueError("Message is required in the request body")
        if not k:
            raise ValueError("k is required in the request body")
        if not aws_parameters:
            raise ValueError("AWS parameters are required in the request body")

        logger.info("Received request to get similar documents for message: %s", message)
        api_parameters = get_api_parameters(aws_parameters)
        openai_client = OpenAI(api_key=api_parameters["openai_api_key"], organization=api_parameters["openai_org_id"])
        pinecone_index = init_pinecone_index(
            api_key=api_parameters["pinecone_api_key"],
            pinecone_env=api_parameters["pinecone_env"],
            pinecone_index=api_parameters["pinecone_index"]
        )
        logger.info("Initialized OpenAI client and Pinecone index")

        # Preprocess the message and create the search queries.
        logger.info("Preprocessing the message and creating search queries")
        enhanced_message = preprocess_message(message)
        logger.info(f"Preprocessing was successful!. Enhanced message:\n\n{enhanced_message}")
        search_queries = [
            f"Seligman theory research findings {enhanced_message}",
            f"Seligman psychological concepts methodology {enhanced_message}",
            f"Seligman research implications applications {enhanced_message}",
            f"Seligman psychology contributions development {enhanced_message}"
        ]

        logger.info("Getting embeddings for the search queries from OpenAI.")
        try:
            embeddings = get_embeddings_batch(openai_client, search_queries)
        except Exception as e:
            logger.exception("An error occurred while getting embeddings from OpenAI: %s", e)
            raise RuntimeError("An error occurred while getting embeddings from OpenAI.") from e
        logger.info("Embeddings retrieval was successful!")


        logger.info("Querying the Pinecone index for similar documents.")
        all_results = []
        for idx, embedding in enumerate(embeddings):
            try:
                results = query_pinecone_index(pinecone_index, embedding, k)
                all_results.extend(results["matches"])

                # Add a 500ms delay between queries to avoid rate limiting
                if idx < len(embeddings) - 1:
                    time.sleep(0.5)
            except Exception as e:
                logger.exception("An error occurred while querying the Pinecone index for query %s: %s", idx+1, e)
                raise RuntimeError("An error occurred while querying the Pinecone index.") from e
        logger.info("Querying the Pinecone index was successful!")

        # Use title as a key for deduplication
        logger.info("Deduplicating the similar documents based on the title")
        seen_titles = {}
        for match in all_results:
            title = match["metadata"].get("title", "").strip()
            if title not in seen_titles or match["score"] > seen_titles[title]["score"]:
                logger.info(f"Match for title:\n{match['metadata']}")
                author = match['metadata'].get('author', 'Unknown')
                year = format_citation_date(match['metadata'].get('year', 'n.d.'))

                seen_titles[title] = {
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'citation_info': {
                        'author': author,
                        'year': year,
                        'title': title
                    }
                }
        logger.info("Deduplication was successful!")

        # Sort by score and create sequential citations
        logger.info("Sorting the similar documents by score and creating sequential citations")
        sorted_results = sorted(seen_titles.values(), key=lambda x: x['score'], reverse=True)[:k]
        citations = {}
        final_results = []
        for idx, result in enumerate(sorted_results, 1):
            citation_id = f"[{idx}]"
            citation = f"{result['citation_info']['author']} ({result['citation_info']['year']}). {result['citation_info']['title']}"

            citations[citation_id] = citation
            final_results.append({
                'score': result['score'],
                'content': result['content'],
                'citation_id': citation_id
            })
        logger.info("Sorting and citation creation was successful!")

        logger.info("Returning response to the client.")
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "matches": final_results,
                "citations": citations
            })
        }
    except Exception as e:
        logger.error("An error occurred while getting the similar documents: %s", e)
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }
