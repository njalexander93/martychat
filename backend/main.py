"""Main module for the FastAPI application.

This module sets up the FastAPI application, including middleware and routes.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.1"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from marty.marty import router as marty_router
from utils.logger import logger

ENV = os.getenv("ENV", "development")
if ENV not in ["development", "production"]:
    logger.error("ENV environment variable must be either 'development' or 'production'")
    raise ValueError("ENV environment variable must be either 'development' or 'production'")
else:
    env_file = f".env.{ENV}"

logger.info(f"Loading environment variables from .env")
load_dotenv(".env")
if os.path.exists(env_file):
    logger.info(f"Loading environment variables from {env_file}")
    load_dotenv(env_file, override=True)
if os.path.exists(".env.local"):
    logger.info(f"Loading environment variables from .env.local")
    load_dotenv(".env.local", override=True)

# Check that the NEXT_PUBLIC_FRONTEND_URL environment variable is set in .env
if "NEXT_PUBLIC_FRONTEND_URL" not in os.environ:
    logger.error("NEXT_PUBLIC_FRONTEND_URL environment variable must be set")
    raise ValueError("NEXT_PUBLIC_FRONTEND_URL environment variable must be set")

# Create the FastAPI app
app = FastAPI(title="Marty Chatbot API", version=__version__, description="API for the Marty Chatbot")

# Add CORS middleware to allow requests from the frontend
allowed_origins = [
    "http://localhost:3000",     # Local development
    "http://127.0.0.1:3000",
    os.getenv("NEXT_PUBLIC_FRONTEND_URL")
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS middleware enabled for origins {allowed_origins}")

app.include_router(marty_router, prefix="/api/v1")
logger.info(f"API routes added to FastAPI app.")

@app.get("/")
def read_root() -> dict:
    """Root endpoint that returns a message confirming that the FastAPI app is running.

    Returns:
        dict: A dictionary containing a confirmation that the FastAPI app is running.
    """
    return {"message": "FastAPI is running... Hello World!"}
