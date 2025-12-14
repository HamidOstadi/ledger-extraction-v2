# src/utils.py

import os
from typing import Optional

from dotenv import load_dotenv  # make sure python-dotenv is installed


def load_env(dotenv_path: Optional[str] = None) -> None:
    """
    Load environment variables from a .env file.
    If dotenv_path is None, it loads from the default location.
    This should be called once at the start of the program/notebook.
    """
    load_dotenv(dotenv_path)


def get_openai_api_key() -> str:
    """
    Retrieve the OpenAI API key from environment variables.

    Expects the key to be stored under the name 'OPENAI_API_KEY'.
    Raises a RuntimeError if the key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it to your .env file or environment."
        )
    return api_key
