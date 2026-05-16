"""
Test for docs_validator.py and mkdocs_exporter.py
This test validates the normalize_writer_output function and the MkDocs export functionality.

# This test calls watsonx.ai and may consume credits.
# Run only when needed.
"""

import sys
import json
import os
from pathlib import Path

# Add project root to sys.path to enable imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.api.writer.docs_validator import normalize_writer_output
from agents.api.writer.mkdocs_exporter import export_mkdocs_project
from agents.api.writer.writer_agent import build_writer_prompt, run_writer_agent, run_writer_agent_raw


def fake_llm_call(prompt: str) -> str:
    """Fake LLM call for testing writer_agent functions."""
    assert isinstance(prompt, str)
    assert "Input:" in prompt
    return json.dumps([
        {
            "title": "Overview",
            "slug": "overview",
            "order": 1,
            "markdown": "# Overview\n## Project summary\nThe API manages tasks."
        },
        {
            "title": "Architecture",
            "slug": "architecture",
            "order": 2,
            "markdown": "# Architecture\n## General description\nThe application separates routes and services."
        },
        {
            "title": "Business logic",
            "slug": "business-logic",
            "order": 3,
            "markdown": "# Business logic\n## Main flow\nThe logic validates data before creating tasks."
        },
        {
            "title": "Onboarding path",
            "slug": "onboarding-path",
            "order": 4,
            "markdown": "# Onboarding path\n## Recommended reading order\n1. Review main.py\n2. Review routes/items.py"
        }
    ], ensure_ascii=False)


def test_writer_agent():
    """Test the writer_agent functions with a fake LLM call."""
    
    print("\n" + "=" * 80)
    print("Testing writer_agent functions...")
    print("=" * 80)
    
    # Simulate official backend JSON
    input_data = {
        "project_name": "task-manager-api",
        "repo_context": {
            "repo_url": "repository-example",
            "stack": ["Python", "FastAPI"],
            "entrypoints": ["main.py"],
            "important_files": [
                {
                    "path": "main.py",
                    "purpose": "Initializes the FastAPI application."
                },
                {
                    "path": "routes/items.py",
                    "purpose": "Defines HTTP routes related to tasks."
                },
                {
                    "path": "services/item_service.py",
                    "purpose": "Contains business rules for tasks."
                }
            ],
            "dependencies": [
                {
                    "from": "routes/items.py",
                    "to": "services/item_service.py",
                    "relationship": "Routes delegate main logic to the service."
                }
            ]
        },
        "bob_response": {
            "overview": "API to manage tasks.",
            "architecture": "The application separates routes and services.",
            "business_logic": "The main logic validates data before creating tasks.",
            "onboarding_path": "Review main.py, routes/items.py and services/item_service.py.",
            "setup": "Create virtual environment, install dependencies and run the server.",
            "tests": {
                "summary": "Test strategy summary.",
                "normal_cases": ["Create a valid task."],
                "edge_cases": ["Send a task without title."],
                "malicious_cases": ["Input too extensive."],
                "privacy_checks": ["Do not return sensitive information."]
            },
            "docker": {
                "explanation": "Docker allows running the API in a reproducible environment.",
                "dockerfile": "FROM python:3.11-slim",
                "docker_compose": "services:\n  app:\n    build: ."
            }
        }
    }
    
    # Test build_writer_prompt
    print("\nTesting build_writer_prompt...")
    built_prompt = build_writer_prompt(input_data)
    assert isinstance(built_prompt, str), \
        f"Expected built_prompt to be str, got {type(built_prompt)}"
    print("[PASS] build_writer_prompt returns a string")
    
    assert "Input:" in built_prompt, \
        "Expected built_prompt to contain 'Input:'"
    print("[PASS] built prompt contains 'Input:'")
    
    # Test run_writer_agent_raw
    print("\nTesting run_writer_agent_raw...")
    raw_output = run_writer_agent_raw(input_data, fake_llm_call)
    assert isinstance(raw_output, str), \
        f"Expected raw_output to be str, got {type(raw_output)}"
    print("[PASS] run_writer_agent_raw returns a string")
    
    # Test run_writer_agent
    print("\nTesting run_writer_agent...")
    frontend_docs = run_writer_agent(input_data, fake_llm_call)
    assert isinstance(frontend_docs, dict), \
        f"Expected frontend_docs to be dict, got {type(frontend_docs)}"
    print("[PASS] run_writer_agent returns a dict")
    
    # Validate the returned dict has exactly 8 pages
    assert len(frontend_docs["pages"]) == 8, \
        f"Expected 8 pages, got {len(frontend_docs['pages'])}"
    print("[PASS] returned dict has exactly 8 pages")
    
    # Validate project_name
    assert frontend_docs["project_name"] == "task-manager-api", \
        f"Expected project_name 'task-manager-api', got '{frontend_docs['project_name']}'"
    print("[PASS] returned dict has project_name == 'task-manager-api'")
    
    # Extract slugs
    slugs = [page["slug"] for page in frontend_docs["pages"]]
    
    # Validate slug "testing" exists
    assert "testing" in slugs, "slug 'testing' not found"
    print("[PASS] returned dict contains slug 'testing'")
    
    # Validate slug "docker" exists
    assert "docker" in slugs, "slug 'docker' not found"
    print("[PASS] returned dict contains slug 'docker'")
    
    # Validate slug "repo-map" exists
    assert "repo-map" in slugs, "slug 'repo-map' not found"
    print("[PASS] returned dict contains slug 'repo-map'")
    
    print("\n" + "=" * 80)
    print("ALL WRITER_AGENT TESTS PASSED!")
    print("=" * 80)


def test_normalize_writer_output():
    """Test the normalize_writer_output function with simulated data."""
    
    # 1. Simulate Writer Agent output
    raw_agent_output = [
        {
            "title": "Overview",
            "slug": "overview",
            "order": 1,
            "markdown": "# Overview\n## Project summary\nThe API manages tasks.\n## Detected technologies\n* Python\n* FastAPI"
        },
        {
            "title": "Architecture",
            "slug": "architecture",
            "order": 2,
            "markdown": "# Architecture\n## General description\nThe application separates HTTP routes and business services."
        },
        {
            "title": "Business logic",
            "slug": "business-logic",
            "order": 3,
            "markdown": "# Business logic\n## Main flow\nThe logic validates data before creating tasks."
        },
        {
            "title": "Onboarding path",
            "slug": "onboarding-path",
            "order": 4,
            "markdown": "# Onboarding path\n## Recommended reading order\n1. Review main.py\n2. Review routes/items.py\n3. Review services/item_service.py"
        }
    ]
    
    # 2. Simulate official backend JSON
    input_data = {
        "project_name": "task-manager-api",
        "repo_context": {
            "repo_url": "repository-example",
            "stack": ["Python", "FastAPI"],
            "entrypoints": ["main.py"],
            "important_files": [
                {
                    "path": "main.py",
                    "purpose": "Initializes the FastAPI application."
                },
                {
                    "path": "routes/items.py",
                    "purpose": "Defines HTTP routes related to tasks."
                },
                {
                    "path": "services/item_service.py",
                    "purpose": "Contains business rules for tasks."
                }
            ],
            "dependencies": [
                {
                    "from": "routes/items.py",
                    "to": "services/item_service.py",
                    "relationship": "Routes delegate main logic to the service."
                }
            ]
        },
        "bob_response": {
            "overview": "API to manage tasks.",
            "architecture": "The application separates routes and services.",
            "business_logic": "The main logic validates data before creating tasks.",
            "onboarding_path": "Review main.py, routes/items.py and services/item_service.py.",
            "setup": "Create virtual environment, install dependencies and run the server.",
            "tests": {
                "summary": "Test strategy summary.",
                "normal_cases": ["Create a valid task."],
                "edge_cases": ["Send a task without title."],
                "malicious_cases": ["Input too extensive."],
                "privacy_checks": ["Do not return sensitive information."]
            },
            "docker": {
                "explanation": "Docker allows running the API in a reproducible environment.",
                "dockerfile": "FROM python:3.11-slim",
                "docker_compose": "services:\n  app:\n    build: ."
            }
        }
    }
    
    # Convert raw_agent_output to JSON string (as the Writer Agent would output)
    raw_output_string = json.dumps(raw_agent_output, ensure_ascii=False) + " <|end_of_text|>"

    
    # Call the function
    frontend_docs = normalize_writer_output(raw_output_string, input_data)
    
    # Print the result
    print("=" * 80)
    print("1. FINAL FRONTEND JSON:")
    print("=" * 80)
    print(json.dumps(frontend_docs, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    # Validate the result
    print("\nRunning validations for normalize_writer_output...")
    
    # Validate project_name
    assert frontend_docs["project_name"] == "task-manager-api", \
        f"Expected project_name 'task-manager-api', got '{frontend_docs['project_name']}'"
    print("[PASS] project_name is correct")
    
    # Validate documentation_format
    assert frontend_docs["documentation_format"] == "markdown", \
        f"Expected documentation_format 'markdown', got '{frontend_docs['documentation_format']}'"
    print("[PASS] documentation_format is correct")
    
    # Validate pages exists
    assert "pages" in frontend_docs, "pages key not found in result"
    print("[PASS] pages exists")
    
    # Validate pages has exactly 8 pages
    assert len(frontend_docs["pages"]) == 8, \
        f"Expected 8 pages, got {len(frontend_docs['pages'])}"
    print("[PASS] pages has exactly 8 pages")
    
    # Extract slugs
    slugs = [page["slug"] for page in frontend_docs["pages"]]
    
    # Validate slug "testing" exists
    assert "testing" in slugs, "slug 'testing' not found"
    print("[PASS] slug 'testing' exists")
    
    # Validate slug "setup" exists
    assert "setup" in slugs, "slug 'setup' not found"
    print("[PASS] slug 'setup' exists")
    
    # Validate slug "docker" exists
    assert "docker" in slugs, "slug 'docker' not found"
    print("[PASS] slug 'docker' exists")
    
    # Validate slug "repo-map" exists
    assert "repo-map" in slugs, "slug 'repo-map' not found"
    print("[PASS] slug 'repo-map' exists")
    
    # Validate final slug order
    expected_order = [
        "overview", "architecture", "business-logic", "onboarding-path",
        "setup", "testing", "docker", "repo-map"
    ]
    assert slugs == expected_order, \
        f"Expected slug order {expected_order}, got {slugs}"
    print("[PASS] final slug order is correct")
    
    # Validate exports.mkdocs_available is False
    assert frontend_docs["exports"]["mkdocs_available"] is False, \
        f"Expected mkdocs_available False, got {frontend_docs['exports']['mkdocs_available']}"
    print("[PASS] exports.mkdocs_available is False")
    
    # Validate exports.download_url is None
    assert frontend_docs["exports"]["download_url"] is None, \
        f"Expected download_url None, got {frontend_docs['exports']['download_url']}"
    print("[PASS] exports.download_url is None")
    
    # Validate every page has required fields
    for i, page in enumerate(frontend_docs["pages"]):
        assert "title" in page, f"Page {i} missing 'title'"
        assert "slug" in page, f"Page {i} missing 'slug'"
        assert "order" in page, f"Page {i} missing 'order'"
        assert "markdown" in page, f"Page {i} missing 'markdown'"
    print("[PASS] every page has title, slug, order and markdown")
    
    # Validate every markdown starts with "#"
    for i, page in enumerate(frontend_docs["pages"]):
        markdown = page["markdown"].strip()
        assert markdown.startswith("#"), \
            f"Page {i} (slug: {page['slug']}) markdown does not start with '#'"
    print("[PASS] every markdown starts with '#'")
    
    print("\n" + "=" * 80)
    print("ALL NORMALIZE_WRITER_OUTPUT TESTS PASSED!")
    print("=" * 80)
    
    # Now test MkDocs export
    print("\n" + "=" * 80)
    print("Testing MkDocs export...")
    print("=" * 80)
    
    # Call export_mkdocs_project
    mkdocs_result = export_mkdocs_project(frontend_docs)
    
    # Print the MkDocs export result
    print("\n" + "=" * 80)
    print("2. MKDOCS EXPORT RESULT:")
    print("=" * 80)
    print(json.dumps(mkdocs_result, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    # Validate MkDocs export results
    print("\nRunning validations for export_mkdocs_project...")
    
    # Validate mkdocs_available is True
    assert mkdocs_result["mkdocs_available"] is True, \
        f"Expected mkdocs_available True, got {mkdocs_result.get('mkdocs_available')}"
    print("[PASS] mkdocs_result['mkdocs_available'] is True")
    
    # Validate files_generated > 0
    assert mkdocs_result["files_generated"] > 0, \
        f"Expected files_generated > 0, got {mkdocs_result.get('files_generated')}"
    print(f"[PASS] mkdocs_result['files_generated'] = {mkdocs_result['files_generated']} > 0")
    
    # Validate zip_path exists physically
    zip_path = Path(mkdocs_result["zip_path"])
    assert zip_path.exists(), \
        f"ZIP file does not exist at {zip_path}"
    print(f"[PASS] ZIP file exists at {zip_path}")
    
    # Validate MkDocs project directory was created
    project_dir = Path(mkdocs_result["project_dir"])
    assert project_dir.exists() and project_dir.is_dir(), \
        f"MkDocs project directory does not exist at {project_dir}"
    print(f"[PASS] MkDocs project directory exists at {project_dir}")
    
    # Validate mkdocs.yml was created
    mkdocs_yml = project_dir / "mkdocs.yml"
    assert mkdocs_yml.exists() and mkdocs_yml.is_file(), \
        f"mkdocs.yml does not exist at {mkdocs_yml}"
    print(f"[PASS] mkdocs.yml exists at {mkdocs_yml}")
    
    # Validate docs/index.md was created
    index_md = project_dir / "docs" / "index.md"
    assert index_md.exists() and index_md.is_file(), \
        f"docs/index.md does not exist at {index_md}"
    print(f"[PASS] docs/index.md exists at {index_md}")
    
    # Validate docs/testing.md was created
    testing_md = project_dir / "docs" / "testing.md"
    assert testing_md.exists() and testing_md.is_file(), \
        f"docs/testing.md does not exist at {testing_md}"
    print(f"[PASS] docs/testing.md exists at {testing_md}")
    
    # Validate docs/docker.md was created
    docker_md = project_dir / "docs" / "docker.md"
    assert docker_md.exists() and docker_md.is_file(), \
        f"docs/docker.md does not exist at {docker_md}"
    print(f"[PASS] docs/docker.md exists at {docker_md}")
    
    # Validate docs/repo-map.md was created
    repo_map_md = project_dir / "docs" / "repo-map.md"
    assert repo_map_md.exists() and repo_map_md.is_file(), \
        f"docs/repo-map.md does not exist at {repo_map_md}"
    print(f"[PASS] docs/repo-map.md exists at {repo_map_md}")
    
    print("\n" + "=" * 80)
    print("ALL MKDOCS EXPORT TESTS PASSED!")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    test_writer_agent()
    test_normalize_writer_output()

# Made with Bob
