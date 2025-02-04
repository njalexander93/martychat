"""Main module for the FastAPI application.

This module sets up the FastAPI application, including middleware and routes.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> dict:
    """Root endpoint that returns a message confirming that the FastAPI app is running.

    Returns:
        dict: A dictionary containing a confirmation that the FastAPI app is running.
    """
    return {"message": "FastAPI is running... Hello World!"}
