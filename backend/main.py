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

ENV = os.getenv("ENV", "development")
if ENV not in ["development", "production"]:
    raise ValueError("ENV environment variable must be either 'development' or 'production'")
else:
    env_file = f".env.{ENV}"

load_dotenv(".env")
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
if os.path.exists(".env.local"):
    load_dotenv(".env.local", override=True)

# Create the FastAPI app
app = FastAPI(title="Marty Chatbot API", version=__version__, description="API for the Marty Chatbot")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # Local development
        "http://127.0.0.1:3000",
        os.getenv("NEXT_PUBLIC_FRONTEND_URL")
    ],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(marty_router, prefix="/api/v1")

@app.get("/")
def read_root() -> dict:
    """Root endpoint that returns a message confirming that the FastAPI app is running.

    Returns:
        dict: A dictionary containing a confirmation that the FastAPI app is running.
    """
    return {"message": "FastAPI is running... Hello World!"}
