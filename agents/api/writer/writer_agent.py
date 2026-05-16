"""
Writer Agent Module

This module connects the Writer Agent prompt with the validator.
It loads the prompt, appends input data, sends it to an LLM via an injected
callable, and normalizes the output using the docs_validator.

The module is framework-agnostic and does not contain any API keys,
credentials, or direct LLM calls. The actual model call is injected
through the llm_call parameter.
"""

from pathlib import Path
import json
from typing import Callable

from agents.api.writer.docs_validator import normalize_writer_output


def load_writer_prompt() -> str:
    """
    Load the Writer Agent prompt from writer_agent_prompt.md.
    
    Returns:
        str: The content of the Writer Agent prompt file.
        
    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_path = Path(__file__).parent / "writer_agent_prompt.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Writer Agent prompt file not found at: {prompt_path}"
        )
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_writer_prompt(input_data: dict) -> str:
    """
    Build the final Writer Agent prompt by appending input data to the base prompt.
    
    Args:
        input_data: Dictionary containing the backend input JSON data.
        
    Returns:
        str: The complete prompt with appended input data.
    """
    base_prompt = load_writer_prompt()
    
    # Format input data as JSON
    formatted_input = json.dumps(input_data, indent=2, ensure_ascii=False)
    
    # Append input data to base prompt
    final_prompt = f"{base_prompt}\n\nInput:\n\n{formatted_input}"
    
    return final_prompt


def run_writer_agent_raw(input_data: dict, llm_call: Callable[[str], str]) -> str:
    """
    Run the Writer Agent and return raw output without normalization.
    
    Args:
        input_data: Dictionary containing the backend input JSON data.
        llm_call: Callable that takes a prompt string and returns the LLM response.
        
    Returns:
        str: The raw output from the LLM call.
    """
    # Build the final prompt
    final_prompt = build_writer_prompt(input_data)
    
    # Call the injected LLM function
    raw_output = llm_call(final_prompt)
    
    # Ensure output is a string
    if not isinstance(raw_output, str):
        raw_output = str(raw_output)
    
    return raw_output


def run_writer_agent(input_data: dict, llm_call: Callable[[str], str]) -> dict:
    """
    Run the Writer Agent and return normalized frontend documentation.
    
    This is the main entry point for using the Writer Agent. It builds the prompt,
    calls the LLM, and normalizes the output into the expected frontend format.
    
    Args:
        input_data: Dictionary containing the backend input JSON data.
        llm_call: Callable that takes a prompt string and returns the LLM response.
        
    Returns:
        dict: The normalized frontend documentation dictionary.
        
    Example:
        >>> from agents.api.writer.writer_agent import run_writer_agent
        >>> frontend_docs = run_writer_agent(input_data, real_llm_call)
    """
    # Build the final prompt
    final_prompt = build_writer_prompt(input_data)
    
    # Call the injected LLM function
    raw_output = llm_call(final_prompt)
    
    # Ensure output is a string
    if not isinstance(raw_output, str):
        raw_output = str(raw_output)
    
    # Normalize the output using the validator
    normalized_output = normalize_writer_output(raw_output, input_data)
    
    return normalized_output

# Made with Bob
