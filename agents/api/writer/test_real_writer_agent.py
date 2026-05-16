"""
Real Writer Agent test using watsonx.ai.

This test calls the real watsonx.ai model using:
input_data -> writer_agent.py -> watsonx.ai -> docs_validator.py -> frontend_docs

Run only when you want to spend credits.

# This test calls watsonx.ai and may consume credits.
# Run only when needed.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.api.writer.writer_agent import run_writer_agent
from agents.api.writer.watsonx_writer_client import watsonx_llm_call
from agents.api.writer.mkdocs_exporter import export_mkdocs_project

def main() -> None:
    input_data = {
  "project_name": "Sistema de Gestión de Usuarios e Imágenes",
  "repo_context": {
    "repo_url": "",
    "stack": [],
    "entrypoints": [],
    "important_files": [],
    "dependencies": []
  },
  "bob_response": {
    "overview": "This repository appears to be a web application framework implementing user management features along with image processing capabilities. It includes modules for handling user authentication, profile management, image segmentation using machine learning models, database interactions, API routing, and caching.",
    "architecture": "The system follows a modular architecture where different concerns are separated into distinct classes. The UserController handles user-related functionalities like registration, authentication, and profile management. ImageProcessor is responsible for image segmentation tasks using machine learning models. DatabaseManager manages database connections and queries. APIRouter routes HTTP requests to appropriate handlers based on registered paths. CacheManager provides caching mechanisms to improve performance. The architecture employs inheritance (e.g., UserController inherits from BaseController) and utilizes object-oriented principles to encapsulate related functionalities.",
    "business_logic": "The core business logic revolves around user management and image processing workflows. Users can register, authenticate, and manage their profiles through the UserController. Authentication involves verifying user credentials and returning session tokens. Profile updates require validation and persistence in the database via DatabaseManager. ImageProcessor handles image segmentation tasks by configuring processing parameters, loading ML models, validating images, and executing segmentation either individually or in batches. Data flows through these components via method calls, with dependencies injected where necessary (e.g., UserController depends on DatabaseManager). Caching is employed to store frequently accessed data, reducing database load and improving response times.",
    "onboarding_path": [
      "Start with understanding the overall structure by reviewing the code map provided.",
      "Read through the global functions section to grasp initialization and setup processes.",
      "Examine the class definitions starting with BaseController if available, then move to UserController to understand user-related functionalities.",
      "Proceed to ImageProcessor to learn about image segmentation capabilities.",
      "Study DatabaseManager to comprehend how data persistence is handled.",
      "Review APIRouter to see how requests are routed to appropriate handlers.",
      "Finally, explore CacheManager to understand caching strategies."
    ],
    "setup": "To set up the development environment:",
    "tests": {
      "summary": "The testing strategy should cover unit tests for individual components, integration tests for component interactions, and end-to-end tests for complete workflows. Mocking frameworks may be needed for isolating external dependencies like databases and ML models.",
      "normal_cases": [
        "Successful user registration and login",
        "Correct image segmentation results for standard inputs"
      ],
      "edge_cases": [
        "Handling invalid user inputs during registration",
        "Processing images with unusual formats or dimensions"
      ],
      "malicious_cases": [
        "Attempting SQL injection through user inputs",
        "Uploading maliciously crafted images to exploit vulnerabilities"
      ],
      "privacy_checks": [
        "Ensuring sensitive user data is properly sanitized and protected",
        "Validating that personal information is not leaked in responses"
      ]
    },
    "docker": {
      "explanation": "Containerization would involve creating Dockerfiles for each service/component, defining base images, copying necessary files, setting up environments, exposing ports, and specifying entry points. A docker-compose.yml file would orchestrate multi-container setups, defining services, networks, volumes, and configurations.",
      "dockerfile": "",
      "docker_compose": ""
    }
  }
}

    print("Running real Writer Agent with watsonx.ai...")
    frontend_docs = run_writer_agent(input_data, watsonx_llm_call)

    print("\nFINAL FRONTEND DOCS:")
    print("=" * 80)
    print(json.dumps(frontend_docs, indent=2, ensure_ascii=False))
    print("=" * 80)

    pages = frontend_docs.get("pages", [])
    slugs = [page.get("slug") for page in pages]

    expected_slugs = [
        "overview",
        "architecture",
        "business-logic",
        "onboarding-path",
        "setup",
        "testing",
        "docker",
        "repo-map"
    ]

    assert frontend_docs["project_name"] == "Sistema de Gestión de Usuarios e Imágenes"
    assert frontend_docs["documentation_format"] == "markdown"
    assert len(pages) == 8
    assert slugs == expected_slugs

    for page in pages:
        assert page["markdown"].strip().startswith("#")

    print("\nALL REAL WRITER AGENT TESTS PASSED!")

    print("\nExporting real frontend docs to MkDocs...")
    mkdocs_result = export_mkdocs_project(frontend_docs)

    print("\nREAL MKDOCS EXPORT RESULT:")
    print("=" * 80)
    print(json.dumps(mkdocs_result, indent=2, ensure_ascii=False))
    print("=" * 80)

    assert mkdocs_result["mkdocs_available"] is True
    assert mkdocs_result["files_generated"] > 0
    assert Path(mkdocs_result["zip_path"]).exists()
    assert Path(mkdocs_result["project_dir"]).exists()

    print("\nALL REAL MKDOCS EXPORT TESTS PASSED!")

if __name__ == "__main__":
    main()