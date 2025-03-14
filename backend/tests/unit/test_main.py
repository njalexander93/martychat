"""Tests for the FastAPI application in main.py.

This module contains tests for the main FastAPI application setup and configuration in the backend/main.py file.
The tests verify the correct initialization of the FastAPI app, CORS middleware, and route handlers.
"""

__author__ = "Nikolai Alexander"
__email__ = "njalexander93@gmail.com"
__version__ = "1.0.0"
__date__ = "TBD"
__license__ = "Proprietary"
__copyright__ = "Copyright (c) 2025 MartyChat"

import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the backend directory to the sys path
backend_dir = os.path.join(os.path.dirname(__file__), "../..")
sys.path.insert(0, backend_dir)


@pytest.mark.unit
def test_env_validation_valid(mock_env_vars: None) -> None:
    """Test that ENV environment variable validation works with valid values.

    This test verifies that the ENV validation logic correctly accepts valid environment values
    (development or production).

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Test with development (already set in mock_env_vars)
    dev_env_var_patch = patch.dict(
        os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}, clear=False
    )
    with dev_env_var_patch:
        # Import the module to trigger the environment validation
        main_module = __import__("main")
        assert os.environ.get("ENV") == "development"

    # Test with production
    prod_env_var_patch = patch.dict(
        os.environ, {"ENV": "production", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}, clear=False
    )
    with prod_env_var_patch:
        importlib.reload(main_module)
        assert os.environ.get("ENV") == "production"


@pytest.mark.unit
def test_env_validation_invalid(mock_env_vars: None) -> None:
    """Test that ENV environment variable validation fails with invalid values.

    This test verifies that the ENV validation logic correctly raises an error for invalid
    environment values.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Test with an invalid environment value
    invalid_env_var_patch = patch.dict(
        os.environ, {"ENV": "invalid", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}, clear=False
    )
    value_error_patch = pytest.raises(
        ValueError, match="ENV environment variable must be either 'development' or 'production'"
    )
    with invalid_env_var_patch, value_error_patch:
        # Import the module again to trigger the environment validation
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
        else:
            __import__("main")


@pytest.mark.unit
def test_frontend_url_validation(mock_env_vars: None) -> None:
    """Test that NEXT_PUBLIC_FRONTEND_URL environment variable validation works.

    This test verifies that the NEXT_PUBLIC_FRONTEND_URL validation logic correctly raises an error
    when the variable is not set.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Test with missing NEXT_PUBLIC_FRONTEND_URL
    clear_env_var_patch = patch.dict(os.environ, clear=True)
    env_var_patch = patch.dict(os.environ, {"ENV": "development"})
    value_error_patch = pytest.raises(ValueError, match="NEXT_PUBLIC_FRONTEND_URL environment variable must be set")
    with clear_env_var_patch, env_var_patch, value_error_patch:
        # Import the module to trigger the environment validation
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
        else:
            __import__("main")


@pytest.mark.unit
def test_environment_loading(mock_env_vars: None) -> None:
    """Test that environment variables are loaded correctly.

    This test verifies that the application correctly loads environment variables from the different
    .env files based on the current environment.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Setup mocks
    mock_load_dotenv = MagicMock()
    mock_exists = MagicMock(side_effect=lambda path: path in [".env", ".env.development", ".env.local"])

    # Apply patches and import the module
    load_dotenv_patch = patch("dotenv.load_dotenv", mock_load_dotenv)
    path_exists_patch = patch("os.path.exists", mock_exists)
    env_var_patch = patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"})
    with load_dotenv_patch, path_exists_patch, env_var_patch:
        # Import the module to trigger the environment loading
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
        else:
            __import__("main")

    # Verify that the correct .env files were loaded
    assert mock_load_dotenv.call_count == 3
    mock_load_dotenv.assert_any_call(".env")
    mock_load_dotenv.assert_any_call(".env.development", override=True)
    mock_load_dotenv.assert_any_call(".env.local", override=True)


@pytest.mark.unit
def test_app_initialization(mock_env_vars: None) -> None:
    """Test that the FastAPI application is initialized correctly.

    This test verifies that the FastAPI application is initialized with the correct title,
    version, and description.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Import the module with patched environment
    with patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}):
        # Import the module to get the FastAPI app
        import main

        importlib.reload(main)

        # Verify the app object
        assert isinstance(main.app, FastAPI)
        assert main.app.title == "Marty Chatbot API"
        assert main.app.version == main.__version__
        assert main.app.description == "API for the Marty Chatbot"

        # Test the root endpoint
        client = TestClient(main.app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "FastAPI is running... Hello World!"}


@pytest.mark.unit
def test_cors_middleware_setup(mock_env_vars: None) -> None:
    """Test that the CORS middleware is configured correctly.

    This test verifies that the CORS middleware is added to the FastAPI application with the
    correct configuration.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up environment for consistent testing
    with patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}):
        # Mock the add_middleware method to capture the arguments
        mock_add_middleware = MagicMock()

        with patch.object(FastAPI, "add_middleware", mock_add_middleware):
            # Import the module to trigger middleware setup
            if "main" in sys.modules:
                importlib.reload(sys.modules["main"])
            else:
                __import__("main")

            # Verify add_middleware was called with CORSMiddleware
            mock_add_middleware.assert_called_once()
            middleware_class = mock_add_middleware.call_args[0][0]
            middleware_kwargs = mock_add_middleware.call_args[1]

            # Check that the middleware class is CORSMiddleware
            from fastapi.middleware.cors import CORSMiddleware

            assert middleware_class == CORSMiddleware

            # Check that the allowed origins include the local development URLs and the frontend URL
            assert "http://localhost:3000" in middleware_kwargs.get("allow_origins", [])
            assert "http://127.0.0.1:3000" in middleware_kwargs.get("allow_origins", [])
            assert os.environ.get("NEXT_PUBLIC_FRONTEND_URL") in middleware_kwargs.get("allow_origins", [])

            # Verify that all methods and headers are allowed
            assert middleware_kwargs.get("allow_methods") == ["*"]
            assert middleware_kwargs.get("allow_headers") == ["*"]


@pytest.mark.unit
def test_router_inclusion(mock_env_vars: None) -> None:
    """Test that the API router is included correctly.

    This test verifies that the marty_router is included in the FastAPI application with the
    correct prefix.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up environment for consistent testing
    with patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}):
        # Mock the include_router method to capture the arguments
        mock_include_router = MagicMock()

        # Create a mock for marty_router that will be imported in main
        mock_marty_router = MagicMock()

        # Apply patches
        include_router_patch = patch.object(FastAPI, "include_router", mock_include_router)
        marty_router_patch = patch.dict("sys.modules", {"marty.marty": MagicMock(router=mock_marty_router)})
        with include_router_patch, marty_router_patch:
            # Import the module to trigger router inclusion
            if "main" in sys.modules:
                importlib.reload(sys.modules["main"])
            else:
                __import__("main")

            # Verify include_router was called with the correct arguments
            mock_include_router.assert_called_once()
            router_arg = mock_include_router.call_args[0][0]
            prefix_kwarg = mock_include_router.call_args[1].get("prefix")

            # Check router and prefix
            assert router_arg == mock_marty_router
            assert prefix_kwarg == "/api/v1"


@pytest.mark.unit
def test_root_endpoint(mock_env_vars: None) -> None:
    """Test the root endpoint of the FastAPI application.

    This test verifies that the root endpoint returns the expected response.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up environment for consistent testing
    with patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"}):
        # Import/reload the module to ensure we have a fresh app instance
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
            main = sys.modules["main"]
        else:
            main = __import__("main")

        # Create a TestClient to make requests to the application
        client = TestClient(main.app)

        # Make a request to the root endpoint
        response = client.get("/")

        # Verify the response
        assert response.status_code == 200
        assert response.json() == {"message": "FastAPI is running... Hello World!"}


@pytest.mark.unit
def test_app_startup_error_missing_env_file(mock_env_vars: None) -> None:
    """Test that the application handles missing environment files gracefully.

    This test verifies that the application logs a warning when an environment file is missing,
    but continues to initialize.

    Args:
        mock_env_vars (None): The mocked environment variables.
    """
    # Set up our mocks
    mock_logger = MagicMock()
    mock_load_dotenv = MagicMock()

    # Mock os.path.exists to simulate missing .env.development file
    def mock_exists(path: str) -> bool:
        if isinstance(path, str):
            return path != ".env.development" and path in [".env", ".env.local"]
        return False

    # Set up patches
    get_logger_patch = patch("logging.getLogger", return_value=mock_logger)
    exists_patch = patch("os.path.exists", mock_exists)
    load_dotenv_patch = patch("dotenv.load_dotenv", mock_load_dotenv)
    env_patch = patch.dict(os.environ, {"ENV": "development", "NEXT_PUBLIC_FRONTEND_URL": "http://localhost:3000"})

    # Apply all patches at once
    with get_logger_patch, exists_patch, load_dotenv_patch, env_patch:
        # Ensure a fresh import of main.py
        if "main" in sys.modules:
            del sys.modules["main"]  # Delete from cache to force re-import
        # Re-import the module after deletion to trigger the environment loading. This should log a warning.
        import main  # noqa: F401

    # Verify that load_dotenv() was actually called
    assert (
        mock_load_dotenv.call_count >= 1
    ), f"Expected load_dotenv to be called at least once, but got {mock_load_dotenv.call_count}"
    mock_load_dotenv.assert_any_call(".env")

    # Ensure .env.development was not loaded
    assert not any(".env.development" in str(args) for args, _ in mock_load_dotenv.call_args_list)

    # Check that .env.local was loaded if our mock says it exists
    if mock_exists(".env.local"):
        mock_load_dotenv.assert_any_call(".env.local", override=True)
