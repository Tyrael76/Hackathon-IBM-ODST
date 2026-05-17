# Hackathon-IBM-ODST
# KAIROS

![Python](https://img.shields.io/badge/Python-FastAPI-blue)
![Flask](https://img.shields.io/badge/Frontend-Flask-green)
![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-purple)
![CrewAI](https://img.shields.io/badge/Agents-CrewAI-orange)
![LangChain](https://img.shields.io/badge/Framework-LangChain-yellow)

## 🧭 Overview

This system is an AI-powered system that automatically transforms GitHub repositories into comprehensive, structured technical documentation. The system combines deterministic code compression with IBM watsonx.ai cognitive analysis to generate professional Markdown documentation including architecture diagrams, security audits, technical debt analysis, and onboarding guides.

## 🎯 Problem It Solves

Software repositories often lack clear, updated documentation, creating significant challenges:

- **Developer Onboarding:** New team members spend excessive time understanding architecture and system flow.
- **Code Maintenance:** Missing context about technical decisions and dependencies.
- **Architecture Understanding:** Absence of diagrams or explanations of module interactions.
- **Security Awareness:** Undetected vulnerabilities and exposed credentials.
- **Technical Debt:** Accumulation of antipatterns and code quality issues without visibility.

## 🚀 Objective

Generate automatic, structured, AI-powered technical documentation from any GitHub repository. The system analyzes source code, identifies architectural patterns, extracts dependencies, detects security vulnerabilities, and produces navigable Markdown documentation with Mermaid.js diagrams, reducing the time needed to understand complex projects from days to minutes.

## 🏗️ System Architecture

The system follows a modular pipeline architecture with clear separation between deterministic processing and AI-based analysis:

### 📥 1. Repository Ingestion Module

**Responsibility:** Download repository files from GitHub and apply intelligent filtering.

**Main files:**

- `fetch_github_repo_tool.py`: Agent-compatible ingestion tool.
- `gitAPI.py`: Core extraction engine with MIME-type filtering.

**Operation:**

- Downloads repository files using GitHub API (PyGithub).
- Applies intelligent MIME-type filtering to discard binaries, images, and compiled files.
- Excludes common non-useful directories (`node_modules`, `__pycache__`, `.git`, `.venv`, etc.).
- Limits file size to 150KB to optimize processing.
- Implements local caching to avoid redundant API calls.
- Extracts basic import dependencies for context.

**Output:** Filtered file structure ready for compression.

### 🧩 2. Structural Compression Module

**Responsibility:** Reduce code volume before sending to AI to optimize token consumption and cost.

**Main files:**

- `agents/compression_path/parser_core.py`: Main compression pipeline orchestrator.
- `agents/compression_path/parser_py.py`: AST analyzer for Python files.
- `agents/compression_path/parser_regex.py`: Pattern analyzer for other languages.

**Operation:**

- **For Python:** Uses AST (Abstract Syntax Tree) analysis to extract classes, functions, methods, inheritance, and docstrings without executing code.
- **For other languages (JS, TS, Java, Kotlin, C#):** Applies regex-based pattern analysis to identify functions, classes, and API endpoints.
- Generates compressed intermediate JSON with code structure.
- Uses concurrent processing (ThreadPoolExecutor) to optimize analysis of large repositories.
- Implements context window protection with automatic fragmentation if JSON exceeds safe limits (100K characters).
- Supports multi-worker parallel processing (configurable, defaults to CPU count).

**Output:** `agents/compression_path/para_uriel.json` - Compressed code structure JSON.

### 🤖 3. AI Technical Analysis Module (CrewAI)

**Responsibility:** Analyze compressed code using IBM watsonx.ai to generate structured technical analysis.

**Main files:**

- `agents/crew_agents.py`: CrewAI orchestration with parallel task execution.
- `main.py`: FastAPI REST API exposing analysis endpoints.

**Operation:**

- Receives compressed JSON from `parser_core`.
- Uses CrewAI framework with two specialized agents:
  - **Auditor Agent:** Technical architect and security expert (analyzes architecture, security, technical debt).
  - **Writer Agent:** Technical writer (generates documentation, diagrams, onboarding guides).
- Executes analysis tasks in parallel using ThreadPoolExecutor for performance.
- Implements LLM response caching to avoid duplicate API calls.
- Uses IBM watsonx.ai with `ibm/granite-8b-code-instruct` model.
- Generates analysis for selected sections:
  - Overview (technologies, project summary).
  - Architecture (components, Mermaid.js diagrams).
  - Business Logic (core processes, entities).
  - Onboarding Path (recommended reading order).
  - Security Audit (OWASP vulnerabilities, exposed secrets).
  - Technical Debt (antipatterns, refactoring suggestions).

**Output:** Structured documentation pages in JSON format ready for frontend consumption.

### 📄 4. Documentation Generation Module

**Responsibility:** Generate complete technical documentation in Markdown format with mitigation guides.

**Main files:**

- `agents/crew_agents.py`: `generate_full_documentation()` function.
- `agents/api/writer/writer_service.py`: Documentation generation service.
- `agents/api/writer/writer_agent.py`: Writer agent orchestration.
- `agents/api/writer/watsonx_writer_client.py`: watsonx.ai client.
- `agents/api/writer/docs_validator.py`: Documentation format validator.

**Operation:**

- Generates complete Markdown documentation from AST analysis.
- Executes documentation sections in parallel for performance.
- Includes mitigation section with actionable remediation commands.
- Supports direct download as `.md` file via `/download-docs` endpoint.
- Validates documentation structure and format.
- Generates Mermaid.js diagrams for architecture visualization.

**Output:** Complete Markdown documentation file ready for download.

### 📦 5. Export Module (Optional)

**Responsibility:** Generate MkDocs projects for offline documentation.

**Main files:**

- `agents/api/writer/mkdocs_exporter.py`: MkDocs project generator.

**Operation:**

- Generates individual Markdown files per section.
- Creates complete MkDocs project with configuration (`mkdocs.yml`).
- Generates downloadable ZIP file with all documentation.
- Stores exports in `generated_exports/`.

**Output:** MkDocs project and ZIP in `generated_exports/`.

### 🖥️ 6. Frontend (Flask)

**Responsibility:** Provide web interface for repository analysis and documentation visualization.

**Main files:**

- `frontend/app.py`: Main Flask application.
- `frontend/routes/main.py`: Frontend routes.
- `frontend/templates/index.html`: Main HTML template.
- `frontend/static/`: CSS and JavaScript resources.

**Operation:**

- Provides web interface for GitHub repository input.
- Allows selection of documentation sections (filters).
- Communicates with FastAPI backend via REST API.
- Renders Markdown to HTML using `marked.js`.
- Renders Mermaid.js diagrams for architecture visualization.
- Provides real-time status updates during analysis.
- Supports full documentation download.

## 🔄 Complete Pipeline Flow

```text
GitHub Repository
        ↓
[1] Repository Ingestion
    (fetch_github_repo_tool.py, gitAPI.py)
    - GitHub API download
    - MIME-type filtering
    - Dependency extraction
        ↓
[2] Structural Compression (Concurrent)
    (parser_core.py, parser_py.py, parser_regex.py)
    - AST analysis (Python)
    - Regex analysis (JS, TS, Java, etc.)
    - Parallel processing
    - Context window protection
        ↓
Compressed JSON
(agents/compression_path/para_uriel.json)
        ↓
[3] AI Analysis (CrewAI + IBM watsonx.ai)
    (crew_agents.py)
    - Auditor Agent (security, architecture, debt)
    - Writer Agent (documentation, diagrams)
    - Parallel task execution
    - LLM caching
        ↓
Documentation Pages JSON
        ↓
[4] Frontend Rendering (Flask)
    (frontend/app.py)
    - Markdown to HTML
    - Mermaid.js diagrams
    - Interactive navigation
        ↓
User Interface
```

## 🔌 API Endpoints

### FastAPI Backend (`main.py` - Port 8000)

#### `POST /extract`

Analyze repository and return documentation pages.

**Input:** `github_token`, `repository`, `branch`, `filters`  
**Output:** JSON with documentation pages.

#### `POST /download-docs`

Generate and download complete Markdown documentation.

**Input:** `github_token`, `repository`, `branch`, `filters`  
**Output:** Streaming Markdown file download.

#### `POST /explain-file`

Explain specific file content.

**Input:** `file_path`, `file_content`  
**Output:** AI-generated explanation.

### Flask Frontend (`frontend/app.py` - Port 5000)

#### `GET /`

Main web interface.

## 🤖 Use of IBM Bob IDE in the Development Process

IBM Bob IDE was used as a central component during the development of this project, not only as a coding assistant, but as an active support tool for architecture planning, agent refactoring, compression logic design, testing, documentation structure, and module integration.

The project required connecting several stages into a single end-to-end workflow: repository ingestion, deterministic code compression, AI-based architectural analysis, technical documentation generation, and frontend visualization. IBM Bob IDE helped the team reason about how these stages should interact and how each module should pass structured information to the next one.

A key architectural decision supported during development was the separation between two major blocks:

- **Deterministic block:** Local Python logic used to ingest, filter, parse, and compress repository files without spending AI tokens. This includes the GitHub ingestion module (`gitAPI.py`, `fetch_github_repo_tool.py`) and the compression pipeline (`parser_core.py`, `parser_py.py`, `parser_regex.py`).

- **Cognitive block:** AI-based reasoning and documentation generation, where IBM Bob and watsonx-based models are used for higher-value tasks. This includes the CrewAI orchestration (`crew_agents.py`) and the Writer module (`agents/api/writer/`).

This separation helped protect the available hackathon budget by avoiding unnecessary AI calls over raw repository content. Instead of sending an entire repository directly to a model, the system first reduces the code into a compact structural representation using AST parsing and regex-based extraction. This allows IBM Bob to focus on understanding architecture, data flow, business logic, and component interaction.

IBM Bob IDE supported the development process in several key areas:

- **Refactoring isolated scripts into a connected modular pipeline:** Helped transform separate proof-of-concept scripts into a cohesive, production-ready system with clear module boundaries and data contracts.

- **Helping define clear JSON contracts between pipeline stages:** Supported the design of intermediate JSON formats (`para_uriel.json`, `paraGio.json`, `frontend_docs.json`) that allow each stage to operate independently.

- **Supporting the isolation of AST-based compression logic and regex fallback extraction:** Assisted in designing the dual-parser approach that handles Python files with AST and other languages with regex patterns.

- **Assisting in the design of the architectural analysis stage:** Helped structure the CrewAI agent system with specialized roles (Auditor and Writer) and parallel task execution.

- **Supporting the Writer stage that transforms analysis into structured Markdown documentation:** Contributed to the design of the documentation generation workflow with proper formatting, Mermaid.js diagram integration, and mitigation sections.

- **Helping define validation logic and test cases for generated documentation:** Supported the creation of the `docs_validator.py` module to ensure consistent output format.

- **Supporting the integration between backend output and frontend rendering:** Helped design the REST API contracts and frontend JavaScript logic for seamless communication.

IBM Bob was especially relevant during refactoring and validation. It helped reason about where each responsibility should live, how the agents should communicate, and how to keep the frontend independent from the internal AI pipeline.

The final output is designed so the frontend does not need to understand how the AI agents work internally. It only consumes the generated documentation structure and renders the Markdown content for the user.

Overall, IBM Bob IDE helped transform the project from separate scripts into a connected, cost-aware, and modular workflow capable of turning a GitHub repository into professional technical documentation.

## 🗂️ Folder Structure

```text
Hackathon-IBM-ODST/
├── agents/                          # Processing modules
│   ├── compression_path/            # Structural code compression
│   │   ├── parser_core.py          # Main pipeline orchestrator
│   │   ├── parser_py.py            # AST analyzer for Python
│   │   ├── parser_regex.py         # Regex analyzer for other languages
│   │   └── para_uriel.json         # Compressed intermediate JSON (generated)
│   ├── api/                         # Analysis and writing modules
│   │   ├── motor.py                # Analysis engine with IBM watsonx.ai
│   │   └── writer/                 # Documentation writer module
│   │       ├── writer_service.py   # Main generation service
│   │       ├── writer_agent.py     # Writer agent orchestration
│   │       ├── watsonx_writer_client.py  # watsonx.ai client
│   │       ├── docs_validator.py   # Documentation validator
│   │       ├── mkdocs_exporter.py  # MkDocs exporter
│   │       └── writer_agent_prompt.md  # Writer agent prompt
│   └── crew_agents.py              # CrewAI orchestration with parallel execution
├── conexiones/                      # Module connectors (legacy)
│   ├── conexion_uriel_antonio.py   # Compression-analysis connector
│   ├── paraGio.json                # Technical analysis JSON (generated)
│   └── frontend_docs.json          # Final JSON for frontend (generated)
├── frontend/                        # Flask web application
│   ├── app.py                      # Main Flask application
│   ├── config.py                   # Frontend configuration
│   ├── routes/                     # Frontend routes
│   │   └── main.py                 # Main route handler
│   ├── templates/                  # HTML templates
│   │   └── index.html              # Main web interface
│   └── static/                     # CSS and JavaScript
│       ├── css/styles.css          # Main stylesheet
│       └── js/                     # JavaScript modules
│           ├── background.js       # Background animations
│           ├── upload.js           # Form handling and API calls
│           └── results.js          # Results rendering
├── generated_exports/               # Generated MkDocs exports (created at runtime)
├── fetch_github_repo_tool.py       # GitHub ingestion tool
├── gitAPI.py                       # Extraction engine with filtering
├── main.py                         # FastAPI REST API (main entry point)
├── requirements.txt                # Project dependencies
└── README.md                       # This file
```

## ✅ Requirements

- Python 3.10 or higher.
- IBM watsonx.ai access: Valid credentials (API key, Project ID, URL).
- GitHub token: Personal Access Token (PAT) with repository read permissions.
- Python dependencies: Installed from `requirements.txt`.

**Important:** IBM watsonx.ai credentials and GitHub token must be configured locally and should never be included in source code or uploaded to the repository.

## 📚 Dependencies

The project uses the following main dependencies grouped by purpose:

### 🧠 IBM watsonx.ai

- `ibm-watsonx-ai>=0.2.0`: Official SDK to interact with IBM watsonx.ai and Granite models.

### ☁️ GitHub/API

- `PyGithub==2.1.1`: Python client for GitHub API.
- `requests>=2.31.0`: HTTP library for API calls.

### 🔌 Backend/API

- `fastapi==0.104.1`: Modern web framework for REST API.
- `uvicorn[standard]==0.24.0`: ASGI server for FastAPI.
- `flask>=3.0.0`: Web framework for frontend.
- `flask-cors>=4.0.0`: CORS handling in Flask.

### 🛡️ Validation

- `pydantic==2.5.0`: Data validation and models.

### 📊 Data Processing

- `pandas>=2.0.0`: Data manipulation and analysis.
- `numpy>=1.24.0`: Numerical operations.

### 🧑‍💻 AI Agents

- `langchain>=0.0.335,<0.0.336`: Framework for LLM applications.
- `langchain-core>=0.1.0`: LangChain core components.
- `crewai>=0.1.0`: Framework for collaborative AI agents.

### 📤 Documentation Export

- `mkdocs>=1.5.0`: Static documentation site generator.
- `mkdocs-material>=9.5.0`: Material Design theme for MkDocs.

### 📁 File Handling

- `PyPDF2>=3.0.0`: PDF file reading.
- `python-docx>=1.0.0`: DOCX file reading.

### 🧪 Testing

- `pytest>=7.4.0`: Testing framework.
- `pytest-cov>=4.1.0`: Code coverage for pytest.

### 🛠️ Utilities

- `python-dotenv>=1.0.0`: Load environment variables from files.
- `python-json-logger>=2.0.0`: Structured JSON logging.

## 🔐 Environment Configuration

The project requires local environment variables for IBM watsonx.ai and GitHub. These credentials are sensitive and must be handled carefully.

**Configuration requirements:**

- Credentials must be placed in a local `.env` file at the project root or configured as system environment variables.
- The `.env` file MUST NOT be uploaded to the repository (already included in `.gitignore`).
- Never write tokens or API keys directly in source code.
- Do not share credentials in public repositories, messages, screenshots, or documentation.

**Required environment variables:**

```env
# IBM watsonx.ai credentials
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# GitHub token (provided via frontend, not in .env)
# Users provide their GitHub PAT through the web interface
```

**How to obtain credentials:**

- IBM watsonx.ai: Visit IBM Cloud and create a watsonx.ai project to obtain your API key and Project ID.
- GitHub Token: Visit GitHub Settings > Developer settings > Personal access tokens and generate a new token with `repo` scope.

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Hackathon-IBM-ODST
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
```

**On Windows:**

```bash
venv\Scripts\activate
```

**On macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# .env file (DO NOT COMMIT THIS FILE)
WATSONX_API_KEY=your_watsonx_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

## ▶️ Execution

### 🌐 Backend Execution (FastAPI)

Start the FastAPI server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:

```text
http://localhost:8000
```

**Interactive API documentation:**

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 🖼️ Frontend Execution (Flask)

In a separate terminal, start the Flask frontend:

```bash
cd frontend
python app.py
```

The frontend will be available at:

```text
http://localhost:5000
```

## 📋 Complete Workflow

1. Start the backend (FastAPI on port 8000).
2. Start the frontend (Flask on port 5000).
3. Open browser at `http://localhost:5000`.
4. Enter GitHub token (Personal Access Token with repo read permissions).
5. Enter repository URL (e.g., `https://github.com/user/repository`).
6. Select branch (`main`, `master`, `dev`, etc.).
7. Select documentation sections (filters):
   - Understanding Block: Onboarding Path.
   - Auditing Block: Security Audit, Technical Debt.
   - Generation Block: Overview, Architecture, Business Logic.
   - Documentation Block: Full Documentation (download).
8. Click **"Analyze Repository"**.
9. Wait for analysis (progress shown in real-time).
10. View results in interactive accordion interface.
11. Download full documentation (optional, if selected).

## 📦 Generated Outputs

The system generates several output files during execution:

### Intermediate Files

- `agents/compression_path/para_uriel.json`: Compressed code structure (AST + Regex analysis).
- `conexiones/paraGio.json`: AI-generated technical analysis (legacy, not used in current flow).
- `conexiones/frontend_docs.json`: Final documentation pages for frontend (legacy, not used in current flow).

### Cache Files

- `cache_<owner>_<repo>.json`: Local cache of repository files to avoid redundant GitHub API calls.

### Export Files (Optional)

- `generated_exports/`: MkDocs projects and ZIP files (if MkDocs export is enabled).

### Downloaded Documentation

- `ODST_Technical_Documentation_<owner>_<repo>.md`: Complete Markdown documentation (downloaded via `/download-docs` endpoint).

## 📤 Documentation Export

The system supports two documentation export formats:

### 1. Direct Markdown Download (Recommended)

Use the `/download-docs` endpoint to generate and download complete technical documentation in a single Markdown file:

- Includes all selected sections.
- Contains Mermaid.js diagrams.
- Includes mitigation guide with remediation commands.
- Zero-waste: No intermediate storage, direct streaming download.
- Filename format: `ODST_Technical_Documentation_<owner>_<repo>.md`.

### 2. MkDocs Export (Optional)

The system can generate exportable documentation in MkDocs format using `agents/api/writer/mkdocs_exporter.py`:

- Individual Markdown files per section.
- Complete MkDocs project with configuration (`mkdocs.yml`).
- Downloadable ZIP file with all documentation.
- Stored in `generated_exports/`.

This export allows:

- Offline documentation consultation.
- Download and share generated documentation.
- Integration with existing documentation systems.
- Publishing on GitHub Pages or other static hosting services.

## ⚠️ Important Notes

### 🔒 Security

- Do not upload the `.env` file to the repository (already included in `.gitignore`).
- Do not upload tokens or API keys in any project file.
- Do not write credentials directly in code - Always use environment variables.
- Review that no credentials are exposed before making commits.
- GitHub tokens are provided by users through the web interface and are never stored.

### 💳 Resource Consumption

- The complete workflow consumes IBM watsonx.ai credits on each execution.
- Analysis of large repositories may take several minutes.
- Concurrent processing is optimized with configurable workers (defaults to CPU count, max 8).
- LLM response caching reduces redundant API calls.
- Context window protection prevents token limit errors.

### 🧾 Generated Files

- Generated JSONs (`para_uriel.json`, `paraGio.json`, `frontend_docs.json`) may change each time the pipeline runs.
- If you change the analyzed repository, you must regenerate all outputs.
- Files in `generated_exports/` are overwritten on each execution.
- Cache files (`cache_*.json`) persist between runs to optimize performance.

### 🚧 Known Warnings

- Some deprecation warnings from the IBM watsonx.ai SDK may appear in the console.
- These warnings do not block current system execution.
- It's recommended to update the SDK when stable versions are available.
- Unicode encoding warnings on Windows are handled automatically.

### 🌍 Compatibility

- The system is designed to work on Windows, Linux, and macOS.
- File paths use `pathlib` for cross-platform compatibility.
- Concurrent processing automatically adapts to the number of available CPUs.
- Console output includes Unicode emoji support with fallback handling.

### ⚡ Performance Optimization

- Parallel processing: Uses ThreadPoolExecutor for concurrent file analysis.
- LLM caching: Avoids duplicate API calls with hash-based caching.
- Context window protection: Automatic chunking for large repositories.
- Intelligent filtering: MIME-type based filtering reduces unnecessary processing.
- Local caching: Repository files cached locally to avoid redundant GitHub API calls.

---

**Developed for Hackathon IBM ODST**

Automatic technical documentation system using IBM watsonx.ai, CrewAI, and intelligent code processing.
