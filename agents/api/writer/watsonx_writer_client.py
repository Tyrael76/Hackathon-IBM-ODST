"""
watsonx Writer Client

This module connects the Writer Agent to watsonx.ai using REST API calls.

It provides:
- watsonx_llm_call(prompt: str) -> str

This function is designed to be injected into:

run_writer_agent(input_data, watsonx_llm_call)

Important:
- Do not hardcode credentials.
- Credentials are read from environment variables or from a local .env file.
- The .env file must not be committed to Git.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict
import urllib.error


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"


def load_local_env(env_path: Path = ENV_PATH) -> None:
    """
    Load simple KEY=VALUE pairs from a local .env file into os.environ.

    This avoids requiring python-dotenv as an external dependency.
    Existing environment variables are not overwritten.
    """
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def get_required_env(name: str) -> str:
    """
    Return a required environment variable.

    Raises:
        RuntimeError: if the variable is missing.
    """
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in your .env file or system environment."
        )

    return value


def get_optional_env(name: str, default: str) -> str:
    """
    Return an optional environment variable.
    """
    return os.getenv(name, default)


def request_iam_token(api_key: str) -> str:
    """
    Generate an IBM IAM access token from an IBM Cloud API key.

    Returns:
        IAM bearer token as a string.
    """
    token_url = "https://iam.cloud.ibm.com/identity/token"

    payload = urllib.parse.urlencode(
        {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        token_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)
    except Exception as exc:
        raise RuntimeError(f"Failed to generate IBM IAM token: {exc}") from exc

    access_token = data.get("access_token")

    if not access_token:
        raise RuntimeError(
            "IBM IAM token response did not contain 'access_token'. "
            f"Response keys: {list(data.keys())}"
        )

    return access_token


def build_generation_payload(prompt: str) -> Dict[str, Any]:
    """
    Build the watsonx.ai text generation payload.
    """
    project_id = get_required_env("WATSONX_PROJECT_ID")
    model_id = get_required_env("WATSONX_MODEL_ID")

    max_new_tokens = int(get_optional_env("WATSONX_MAX_NEW_TOKENS", "900"))
    temperature = float(get_optional_env("WATSONX_TEMPERATURE", "0.1"))

    return {
        "model_id": model_id,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "repetition_penalty": 1.05,
            "stop_sequences": ["<|end_of_text|>"],
        },
    }


def extract_generated_text(response_data: Dict[str, Any]) -> str:
    """
    Extract generated text from watsonx.ai response.

    Expected common format:
    {
      "results": [
        {
          "generated_text": "..."
        }
      ]
    }
    """
    results = response_data.get("results")

    if isinstance(results, list) and results:
        first_result = results[0]

        if isinstance(first_result, dict):
            generated_text = first_result.get("generated_text")

            if generated_text is not None:
                return str(generated_text)

    raise RuntimeError(
        "Could not extract generated text from watsonx.ai response. "
        f"Response keys: {list(response_data.keys())}"
    )


def watsonx_llm_call(prompt: str) -> str:
    """
    Send a prompt to watsonx.ai and return only the generated text.

    This function is the real llm_call that can be injected into:

    run_writer_agent(input_data, watsonx_llm_call)
    """
    if not isinstance(prompt, str):
        prompt = str(prompt)

    load_local_env()

    api_key = get_required_env("IBM_API_KEY")
    watsonx_url = get_required_env("WATSONX_URL").rstrip("/")
    version = get_optional_env("WATSONX_VERSION", "2023-05-29")

    token = request_iam_token(api_key)
    payload = build_generation_payload(prompt)

    generation_url = f"{watsonx_url}/ml/v1/text/generation?version={version}"

    request_body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        generation_url,
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
            response_data = json.loads(response_body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"watsonx.ai generation request failed with HTTP {exc.code}: {error_body}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"watsonx.ai generation request failed: {exc}") from exc

    return extract_generated_text(response_data)