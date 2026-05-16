"""
Documentation Validator and Normalizer

This module normalizes the raw Writer Agent output and generates
the final frontend contract with all required documentation pages.

Main function: normalize_writer_output(raw_output: str, input_data: dict) -> dict
"""

import json
import re
from typing import Any, Dict, List, Optional, Union


def clean_raw_output(raw_output: str) -> str:
    """
    Clean raw output from Writer Agent.
    
    Removes:
    - End-of-text tokens like <|end_of_text|>
    - Markdown fences like ```json and ```
    - Replaces harmful text placeholders
    
    Args:
        raw_output: Raw string output from Writer Agent
        
    Returns:
        Cleaned string ready for JSON extraction
    """
    # Remove end-of-text tokens
    cleaned = re.sub(r'<\|end_of_text\|>', '', raw_output)
    
    # Remove markdown code fences
    cleaned = re.sub(r'```json\s*', '', cleaned)
    cleaned = re.sub(r'```\s*', '', cleaned)
    
    # Replace harmful text placeholders
    cleaned = cleaned.replace('[Potentially harmful text removed]', 'No information available.')
    
    # Clean extra whitespace while preserving structure
    cleaned = cleaned.strip()
    
    return cleaned


def extract_first_json(raw_output: str) -> Optional[Union[List, Dict]]:
    """
    Extract the first valid JSON from raw output.
    
    Accepts:
    - JSON array of pages
    - JSON object containing a "pages" key
    
    Args:
        raw_output: Cleaned raw output string
        
    Returns:
        Parsed JSON (list or dict) or None if no valid JSON found
    """
    try:
        # Try to parse the entire string as JSON
        parsed = json.loads(raw_output)
        return parsed
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON array pattern
    array_pattern = r'\[\s*\{.*?\}\s*\]'
    array_match = re.search(array_pattern, raw_output, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object pattern
    object_pattern = r'\{.*?\}'
    object_match = re.search(object_pattern, raw_output, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def clean_markdown_text(markdown: str) -> str:
    """
    Clean markdown text content.
    
    Removes harmful text placeholders and end-of-text tokens.
    
    Args:
        markdown: Markdown content to clean
        
    Returns:
        Cleaned markdown string
    """
    # Convert to string if needed
    markdown = str(markdown)
    
    # Replace harmful text placeholders
    markdown = markdown.replace('[Potentially harmful text removed]', 'No information available.')
    
    # Remove end-of-text tokens
    markdown = markdown.replace('<|end_of_text|>', '')
    
    # Strip surrounding whitespace
    markdown = markdown.strip()
    
    return markdown


def ensure_h1(markdown: str, title: str) -> str:
    """
    Ensure markdown starts with H1 heading.
    
    Args:
        markdown: Markdown content
        title: Page title to use for H1 if missing
        
    Returns:
        Markdown with H1 heading
    """
    markdown = markdown.strip()
    
    # Check if markdown already starts with H1
    if markdown.startswith('# '):
        return markdown
    
    # Prepend H1 with title
    return f"# {title}\n\n{markdown}"


def normalize_page(page: dict, fallback_title: str, fallback_slug: str, fallback_order: int) -> dict:
    """
    Normalize a single page from Writer Agent output.
    
    Validates and ensures all required fields exist.
    
    Args:
        page: Page dictionary from Writer Agent
        fallback_title: Title to use if missing
        fallback_slug: Slug to use if missing
        fallback_order: Order to use if missing
        
    Returns:
        Normalized page dictionary
    """
    title = page.get('title', fallback_title)
    slug = fallback_slug
    order = fallback_order
    markdown = page.get('markdown', 'No information available.')
    
    # Clean markdown text
    markdown = clean_markdown_text(markdown)
    
    # Ensure markdown starts with H1
    markdown = ensure_h1(markdown, title)
    
    return {
        'title': title,
        'slug': slug,
        'order': order,
        'markdown': markdown
    }


def build_setup_page(input_data: dict) -> dict:
    """
    Generate the setup page from input data.
    
    Args:
        input_data: Backend input JSON
        
    Returns:
        Setup page dictionary
    """
    bob_response = input_data.get('bob_response', {})
    setup_text = bob_response.get('setup', 'No information available.')
    
    markdown = f"""# Setup

## General description

{setup_text}

## Suggested steps

1. Review the general project instructions.
2. Prepare the local environment according to the detected dependencies.
3. Run the project following the indicated configuration.
"""
    
    return {
        'title': 'Setup',
        'slug': 'setup',
        'order': 5,
        'markdown': markdown.strip()
    }


def build_testing_page(input_data: dict) -> dict:
    """
    Generate the testing page from input data.
    
    Args:
        input_data: Backend input JSON
        
    Returns:
        Testing page dictionary
    """
    bob_response = input_data.get('bob_response', {})
    tests = bob_response.get('tests', {})
    
    summary = tests.get('summary', 'No information available.')
    
    # Build normal cases list
    normal_cases = tests.get('normal_cases', [])
    if normal_cases:
        normal_list = '\n'.join([f'- {case}' for case in normal_cases])
    else:
        normal_list = '- No information available.'
    
    # Build edge cases list
    edge_cases = tests.get('edge_cases', [])
    if edge_cases:
        edge_list = '\n'.join([f'- {case}' for case in edge_cases])
    else:
        edge_list = '- No information available.'
    
    # Build malicious cases list
    malicious_cases = tests.get('malicious_cases', [])
    if malicious_cases:
        malicious_list = '\n'.join([f'- {case}' for case in malicious_cases])
    else:
        malicious_list = '- No information available.'
    
    # Build privacy checks list
    privacy_checks = tests.get('privacy_checks', [])
    if privacy_checks:
        privacy_list = '\n'.join([f'- {case}' for case in privacy_checks])
    else:
        privacy_list = '- No information available.'
    
    markdown = f"""# Suggested tests

## Summary

{summary}

## Normal cases

{normal_list}

## Edge cases

{edge_list}

## Robustness validations

{malicious_list}

## Privacy checks

{privacy_list}
"""
    
    return {
        'title': 'Suggested tests',
        'slug': 'testing',
        'order': 6,
        'markdown': markdown.strip()
    }


def build_docker_page(input_data: dict) -> dict:
    """
    Generate the docker page from input data.
    
    Args:
        input_data: Backend input JSON
        
    Returns:
        Docker page dictionary
    """
    bob_response = input_data.get('bob_response', {})
    docker = bob_response.get('docker', {})
    
    explanation = docker.get('explanation', 'No information available.')
    dockerfile = docker.get('dockerfile', 'No information available.')
    docker_compose = docker.get('docker_compose', 'No information available.')
    
    markdown = f"""# Docker

## Explanation

{explanation}

## Suggested Dockerfile

```dockerfile
{dockerfile}
```

## Suggested Compose

```yaml
{docker_compose}
```
"""
    
    return {
        'title': 'Docker',
        'slug': 'docker',
        'order': 7,
        'markdown': markdown.strip()
    }


def build_repo_map_page(input_data: dict) -> dict:
    """
    Generate the repo-map page from input data.
    
    Args:
        input_data: Backend input JSON
        
    Returns:
        Repo-map page dictionary
    """
    repo_context = input_data.get('repo_context', {})
    
    repo_url = repo_context.get('repo_url', 'No information available.')
    
    # Build entrypoints list
    entrypoints = repo_context.get('entrypoints', [])
    if entrypoints:
        entrypoints_list = '\n'.join([f'- `{ep}`' for ep in entrypoints])
    else:
        entrypoints_list = '- No information available.'
    
    # Build important files table
    important_files = repo_context.get('important_files', [])
    if important_files:
        files_table = '| File | Purpose |\n|---|---|\n'
        for file in important_files:
            path = file.get('path', '')
            purpose = file.get('purpose', '')
            files_table += f'| `{path}` | {purpose} |\n'
    else:
        files_table = 'No information available.'
    
    # Build dependencies table
    dependencies = repo_context.get('dependencies', [])
    if dependencies:
        deps_table = '| From | To | Relationship |\n|---|---|---|\n'
        for dep in dependencies:
            from_path = dep.get('from', '')
            to_path = dep.get('to', '')
            relationship = dep.get('relationship', '')
            deps_table += f'| `{from_path}` | `{to_path}` | {relationship} |\n'
    else:
        deps_table = 'No information available.'
    
    markdown = f"""# Repository map

## Repository

{repo_url}

## Entry points

{entrypoints_list}

## Important files

{files_table}

## Internal dependencies

{deps_table}
"""
    
    return {
        'title': 'Repository map',
        'slug': 'repo-map',
        'order': 8,
        'markdown': markdown.strip()
    }


def normalize_writer_output(raw_output: str, input_data: dict) -> dict:
    """
    Normalize Writer Agent output and generate final frontend contract.
    
    This is the main function that:
    1. Cleans raw output
    2. Extracts JSON
    3. Normalizes Writer Agent pages (overview, architecture, business-logic, onboarding-path)
    4. Generates deterministic pages (setup, testing, docker, repo-map)
    5. Returns final frontend contract
    
    Args:
        raw_output: Raw string output from Writer Agent
        input_data: Backend input JSON with project context
        
    Returns:
        Final frontend contract dictionary
    """
    # Clean raw output
    cleaned = clean_raw_output(raw_output)
    
    # Extract JSON
    extracted = extract_first_json(cleaned)
    
    # Initialize pages list
    writer_pages = []
    
    if extracted:
        # Handle array format
        if isinstance(extracted, list):
            writer_pages = extracted
        # Handle object format with "pages" key
        elif isinstance(extracted, dict) and 'pages' in extracted:
            writer_pages = extracted['pages']
    
    # Define required interpretive pages
    required_pages = {
        'overview': {'title': 'Overview', 'order': 1},
        'architecture': {'title': 'Architecture', 'order': 2},
        'business-logic': {'title': 'business-logic', 'order': 3},
        'onboarding-path': {'title': 'Onboarding-path', 'order': 4}

    }
    
    # Normalize and filter Writer Agent pages
    normalized_pages = {}
    for page in writer_pages:
        slug = page.get('slug', '')
        if slug in required_pages:
            normalized_pages[slug] = normalize_page(
                page,
                required_pages[slug]['title'],
                slug,
                required_pages[slug]['order']
            )
    
    # Ensure all required pages exist
    final_pages = []
    for slug, config in required_pages.items():
        if slug in normalized_pages:
            final_pages.append(normalized_pages[slug])
        else:
            # Generate missing page with fallback
            final_pages.append({
                'title': config['title'],
                'slug': slug,
                'order': config['order'],
                'markdown': f"# {config['title']}\n\nNo information available."
            })
    
    # Generate deterministic pages
    final_pages.append(build_setup_page(input_data))
    final_pages.append(build_testing_page(input_data))
    final_pages.append(build_docker_page(input_data))
    final_pages.append(build_repo_map_page(input_data))
    
    # Sort pages by order
    final_pages.sort(key=lambda p: p['order'])
    
    # Build final contract
    project_name = input_data.get('project_name', 'unknown-project')
    generated_at = "2026-05-15T00:00:00Z"
    
    return {
        'project_name': project_name,
        'documentation_format': 'markdown',
        'generated_at': generated_at,
        'pages': final_pages,
        'exports': {
            'mkdocs_available': False,
            'download_url': None
        }
    }

# Made with Bob
