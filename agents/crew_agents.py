import os
import json
from typing import Any, List, Optional, Dict
from pydantic import PrivateAttr
from crewai import Agent, Task, Crew, Process
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain.llms.base import LLM
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

load_dotenv()

# Cache global para evitar llamadas duplicadas
_llm_cache = {}

class CustomWatsonxLLM(LLM):
    model_id: str
    
    def __init__(self, model_id: str, **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        api_key = os.getenv("WATSONX_API_KEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        url = os.getenv("WATSONX_URL")

        credentials = {
            "url": url,
            "apikey": api_key
        }

        model_params = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 1500,  # Reducido de 4000 a 1500 para respuestas más rápidas
            GenParams.MIN_NEW_TOKENS: 50,    # Aumentado de 10 a 50 para respuestas más concisas
            GenParams.TEMPERATURE: 0.1,
            GenParams.TOP_K: 50,
            GenParams.TOP_P: 0.95,
            GenParams.REPETITION_PENALTY: 1.1
        }

        # Usar object.__setattr__ para evitar problemas con Pydantic
        object.__setattr__(self, '_model', Model(
            model_id=model_id,
            params=model_params,
            credentials=credentials,
            project_id=project_id
        ))

    @property
    def _llm_type(self) -> str:
        return "custom_watsonx"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        # Implementar caché simple basado en hash del prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        if prompt_hash in _llm_cache:
            print(f"✅ Cache hit for prompt hash: {prompt_hash[:8]}...")
            return _llm_cache[prompt_hash]
        
        response = self._model.generate_text(prompt=prompt)
        if isinstance(response, list):
            result = " ".join(str(item) for item in response)
        else:
            result = str(response)
        
        # Guardar en caché
        _llm_cache[prompt_hash] = result
        return result

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Método invoke requerido por LangChain para compatibilidad con Runnable.
        """
        return self._call(prompt, **kwargs)

# Instantiate models based on requirements - using available models
# granite-8b-code-instruct is used because 3-1-8b-base does not support text generation
auditor_llm = CustomWatsonxLLM(model_id="ibm/granite-8b-code-instruct")
writer_llm = CustomWatsonxLLM(model_id="ibm/granite-8b-code-instruct")

def run_crew_analysis(ast_data: dict, filters: dict) -> List[Dict[str, Any]]:
    auditor = Agent(
        role='Senior Technical Auditor',
        goal='Analyze a repository AST to extract its architecture, business rules, vulnerabilities (OWASP Top 10, exposed tokens) and technical debt.',
        backstory='You are a software architect and cybersecurity expert. You focus on discovering OWASP vulnerabilities, exposed tokens, and hunting design anti-patterns.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=auditor_llm
    )

    writer = Agent(
        role='Senior Technical Writer',
        goal='Consolidate technical reports. For architecture sections, you MUST generate a data flow diagram in Mermaid.js syntax wrapped in a ```mermaid code block.',
        backstory='You are a technical writer expert in Markdown format and data visualization using Mermaid.js.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        llm=writer_llm
    )

    # Create a compact summary of the AST instead of sending everything
    ast_summary = _create_ast_summary(ast_data)
    
    results = []
    
    # Prepare all tasks for parallel execution
    tasks_to_execute = []
    
    if filters.get("overview", False):
        tasks_to_execute.append(("overview", writer, f"Analyze the following project summary and provide a general 'Overview' of its main technologies:\n\n{ast_summary}\n\nDeliver the result in Markdown.", 1))

    if filters.get("architecture", False):
        arch_prompt = (
            f"Analyze the following project structure and deduce the architecture.\n"
            f"You MUST strictly follow this format in Markdown:\n\n"
            f"## Overview\n"
            f"(Brief descriptive paragraph of the architecture)\n\n"
            f"## Main Components\n"
            f"(Bullet point list of key components)\n\n"
            f"## Architecture Diagram\n"
            f"Create a flow diagram using Mermaid.js syntax. Use ONLY these valid Mermaid diagram types:\n"
            f"- graph TD (top-down flowchart)\n"
            f"- graph LR (left-right flowchart)\n"
            f"- sequenceDiagram (for API flows)\n\n"
            f"Example of valid syntax:\n"
            f"```mermaid\n"
            f"graph TD\n"
            f"    A[Frontend] --> B[API]\n"
            f"    B --> C[Database]\n"
            f"    B --> D[External Service]\n"
            f"```\n\n"
            f"IMPORTANT: Use simple node names (A, B, C) and clear labels in brackets. Avoid special characters.\n\n"
            f"Structure:\n{ast_summary}"
        )
        tasks_to_execute.append(("architecture", writer, arch_prompt, 2))

    if filters.get("business-logic", False):
        tasks_to_execute.append(("business-logic", auditor, f"Analyze the following summary and extract the core processes, entities and detected anti-patterns:\n\n{ast_summary}\n\nDeliver the result structured in Markdown.", 3))

    if filters.get("onboarding-path", False):
        tasks_to_execute.append(("onboarding-path", writer, f"Analyze the following summary and provide an 'Onboarding Path' recommending which files to read first:\n\n{ast_summary}\n\nDeliver the result in Markdown.", 4))

    if filters.get("security-audit", False):
        tasks_to_execute.append(("security-audit", auditor, f"Analyze the following summary focusing on cybersecurity. Search for OWASP Top 10 vulnerabilities and exposed secrets:\n\n{ast_summary}\n\nDeliver the result in Markdown.", 5))

    if filters.get("technical-debt", False):
        tasks_to_execute.append(("technical-debt", auditor, f"Analyze the following summary identifying bad practices, anti-patterns and technical debt with refactoring suggestions:\n\n{ast_summary}\n\nDeliver the result in Markdown.", 6))
    
    # Execute all tasks in parallel using ThreadPoolExecutor
    if tasks_to_execute:
        print(f"\n{'='*70}")
        print(f"🤖 [CREW] Starting parallel analysis with {len(tasks_to_execute)} tasks")
        print(f"{'='*70}\n")
        
        with ThreadPoolExecutor(max_workers=min(len(tasks_to_execute), 4)) as executor:
            future_to_task = {}
            for task_info in tasks_to_execute:
                slug, agent, description, order = task_info
                print(f"📋 [CREW] Submitting task: {slug}")
                prompt = f"System: {agent.backstory}\n\nTask: {description}"
                
                try:
                    # Use the LLM's invoke method directly
                    future = executor.submit(agent.llm.invoke, prompt)
                    future_to_task[future] = (slug, order)
                except Exception as submit_error:
                    print(f"❌ [CREW] Failed to submit task {slug}: {str(submit_error)}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Error submitting task: {str(submit_error)}",
                        "data": {}
                    })
            
            for future in as_completed(future_to_task):
                slug, order = future_to_task[future]
                try:
                    print(f"⏳ [CREW] Waiting for result: {slug}")
                    response = future.result(timeout=120)  # 2 minute timeout
                    print(f"✅ [CREW] Completed: {slug}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": str(response),
                        "data": {}
                    })
                except TimeoutError:
                    print(f"⏱️ [CREW] Timeout for task: {slug}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Task timed out after 120 seconds",
                        "data": {}
                    })
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"❌ [CREW] Error in {slug}:")
                    print(f"   Type: {type(e).__name__}")
                    print(f"   Message: {str(e)}")
                    print(f"   Traceback:\n{error_trace}")
                    results.append({
                        "title": slug.replace("-", " ").title(),
                        "slug": slug,
                        "order": order,
                        "markdown": f"Error generating report: {str(e)}\n\nDetails:\n{error_trace}",
                        "data": {}
                    })
        
        print(f"\n{'='*70}")
        print(f"✅ [CREW] All tasks completed: {len(results)} results")
        print(f"{'='*70}\n")
    
    # Sort results by order
    results.sort(key=lambda x: x["order"])
    return results

def _create_ast_summary(ast_data: dict, max_chars: int = 5000) -> str:
    """
    Creates a compact summary of the AST to reduce the context size.
    Extracts only the most relevant information.
    """
    summary_parts = []
    # Extract file structure
    if "files" in ast_data:
        file_list = list(ast_data["files"].keys())[:50]  # First 50 files
        summary_parts.append(f"Files ({len(ast_data['files'])} total): {', '.join(file_list)}")
    
    # Extract main dependencies
    if "dependencies" in ast_data:
        deps = ast_data.get("dependencies", {})
        if deps:
            summary_parts.append(f"Dependencies: {', '.join(list(deps.keys())[:20])}")
    
    # Extract main functions/classes (limited sample)
    if "files" in ast_data:
        main_entities = []
        for file_path, file_data in list(ast_data["files"].items())[:10]:
            if isinstance(file_data, dict):
                if "classes" in file_data:
                    main_entities.extend([f"class {c}" for c in list(file_data["classes"].keys())[:3]])
                if "functions" in file_data:
                    main_entities.extend([f"func {f}" for f in list(file_data["functions"].keys())[:3]])
        if main_entities:
            summary_parts.append(f"Main entities: {', '.join(main_entities[:30])}")
    
    summary = "\n\n".join(summary_parts)
    
    # Truncate if necessary
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n... [TRUNCATED]"
    
    return summary

def generate_full_documentation(ast_data: dict, filters: dict) -> str:
    """
    Generates complete technical documentation in Markdown format using parallel LLM calls.
    Includes a mitigation section at the end with remediation commands.
    
    Args:
        ast_data: AST data of the repository
        filters: Section filters to include
    
    Returns:
        String with the complete Markdown document
    """
    print(f"\n{'='*70}")
    print(f"📄 [DOCUMENTATION] Starting parallel technical documentation generation")
    print(f"{'='*70}\n")
    
    # Create AST summary
    ast_summary = _create_ast_summary(ast_data)
    
    # Prepare sequential tasks for parallel execution
    tasks_to_execute = []
    
    # Document header
    doc_header = f"# Technical Documentation - ODST Analysis\n\n"
    doc_header += f"**Generated by:** ODST (Omniscient Documentation & Security Toolkit)\n\n"
    doc_header += f"---\n\n"
    
    if filters.get("overview", False):
        overview_prompt = (
            f"Analyze the following AST summary of a repository and write the content for the 'Overview' section.\n"
            f"Write a detailed and engaging report in English, using Markdown subtitles (H3: ###), lists and bold text.\n"
            f"You MUST include:\n"
            f"- Project Summary: Clear and user-friendly explanation of what the project does.\n"
            f"- Detected Technologies: What main languages, frameworks, or libraries are used.\n"
            f"- Code Organization: How key folders are organized and what responsibilities they have.\n\n"
            f"Do NOT include the main title '## Overview', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("overview", "Senior Technical Writer", overview_prompt, "## Overview", 1))
    
    if filters.get("architecture", False):
        arch_prompt = (
            f"Analyze the project structure and write the content for the 'System Architecture' section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- General Description: Main design pattern (e.g. MVC, monolith, etc.) and information flow.\n"
            f"- Key Components: Responsibility of each main directory and file.\n"
            f"- Architecture Diagram (Mermaid.js): You MUST create a flow diagram using Mermaid.js syntax wrapped in a ```mermaid block.\n\n"
            f"Do NOT include the main title '## System Architecture', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("architecture", "Senior Technical Writer", arch_prompt, "## System Architecture", 2))
    
    if filters.get("business-logic", False):
        logic_prompt = (
            f"Analyze the project AST and write the content for the 'Business Logic' section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- Core Processes: Main business rules and user flows.\n"
            f"- Entities and Data: Key domain models.\n"
            f"- Information Flow: How functions and services interact.\n\n"
            f"Do NOT include the main title '## Business Logic', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("business-logic", "Senior Technical Auditor", logic_prompt, "## Business Logic", 3))
    
    if filters.get("onboarding-path", False):
        onboarding_prompt = (
            f"Analyze the repository AST and write the content for the 'Onboarding Guide' (Quick Start) section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- Recommended Reading Path: Numbered list of files to read to understand the project.\n"
            f"- Initial Setup: Software requirements and dependencies.\n"
            f"- Local Start: Commands and steps to run the application locally.\n\n"
            f"Do NOT include the main title '## Onboarding Guide', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("onboarding-path", "Senior Technical Writer", onboarding_prompt, "## Onboarding Guide", 4))
    
    if filters.get("security-audit", False):
        security_prompt = (
            f"Analyze the repository AST and write the content for the 'Security Audit' section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- Potential Vulnerabilities: OWASP Top 10 risks (e.g. injections, leaks, etc.).\n"
            f"- Credentials and Secrets: If there is suspicion of API keys or exposed tokens.\n"
            f"- Recommendations: Immediate actions to strengthen the code.\n\n"
            f"Do NOT include the main title '## Security Audit', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("security-audit", "Senior Technical Auditor", security_prompt, "## Security Audit", 5))
    
    if filters.get("technical-debt", False):
        debt_prompt = (
            f"Analyze the repository AST and write the content for the 'Technical Debt' section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- Bad Practices and Anti-patterns: Code with high complexity or obsolete dependencies.\n"
            f"- Modularity: Evaluation of software coupling level.\n"
            f"- Refactoring Plan: Concrete suggestions to improve code quality.\n\n"
            f"Do NOT include the main title '## Technical Debt', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("technical-debt", "Senior Technical Auditor", debt_prompt, "## Technical Debt", 6))
    
    # Mitigation task (always included if security or technical debt is enabled)
    if filters.get("security-audit", False) or filters.get("technical-debt", False):
        mitigation_prompt = (
            f"Based on the AST analysis, write the content for the 'Execution Guide and Mitigation' section.\n"
            f"Write a structured report in English, using subtitles (###).\n"
            f"You MUST include:\n"
            f"- Remediation Commands: Real, copy-pasteable console commands (e.g. `pip-audit`, `bandit -r .`, `black .`, `pylint`).\n"
            f"- Secure Development Practices: Recommendations for day-to-day work.\n"
            f"- Priority Action Plan: List ordered by priority (High, Medium, Low).\n\n"
            f"Do NOT include the main title '## Execution Guide and Mitigation', as it will be added automatically. Start directly with the content.\n\n"
            f"AST Summary:\n{ast_summary}"
        )
        tasks_to_execute.append(("mitigation", "Senior Technical Writer", mitigation_prompt, "## Execution Guide and Mitigation", 7))
    
    if not tasks_to_execute:
        return doc_header + "\n*No sections were selected to generate.*\n"
    
    results = []
    
    try:
        print(f"🚀 [DOCUMENTATION] Starting ThreadPoolExecutor for parallel execution of {len(tasks_to_execute)} tasks")
        
        with ThreadPoolExecutor(max_workers=min(len(tasks_to_execute), 4)) as executor:
            future_to_task = {}
            for task_info in tasks_to_execute:
                slug, role, prompt_text, header, order = task_info
                print(f"📋 [DOCUMENTATION] Submitting task to thread pool: {slug}")
                full_prompt = f"System: You are a {role}. Always act professionally and deliver the structured content in clean, detailed Markdown.\n\nTask: {prompt_text}"
                
                # Execute through LLM's invoke directly (uses global cache if hit matches)
                future = executor.submit(writer_llm.invoke, full_prompt)
                future_to_task[future] = (slug, header, order)
            
            for future in as_completed(future_to_task):
                slug, header, order = future_to_task[future]
                try:
                    print(f"⏳ [DOCUMENTATION] Waiting for parallel result: {slug}")
                    response = future.result(timeout=120)  # 2 minute timeout per task
                    print(f"✅ [DOCUMENTATION] Thread complete: {slug}")
                    
                    # Consolidate result with its correct Markdown title
                    section_content = f"{header}\n\n{str(response)}"
                    results.append((order, section_content))
                except TimeoutError:
                    print(f"⏱️ [DOCUMENTATION] Timeout for task: {slug}")
                    results.append((order, f"{header}\n\n*Error: Generation of this section exceeded the 120-second time limit.*\n"))
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"❌ [DOCUMENTATION] Thread failed: {slug}")
                    print(f"   Message: {str(e)}")
                    results.append((order, f"{header}\n\n*Error generating report: {str(e)}*\n\n```\n{error_trace}\n```\n"))
        
        # Sort results by their sequence order
        results.sort(key=lambda x: x[0])
        
        # Combine header with generated content
        full_doc = doc_header
        for _, content in results:
            full_doc += content + "\n\n"
        
        print(f"✅ [DOCUMENTATION] Documentation generation complete!")
        print(f"   Total length: {len(full_doc)} characters")
        print(f"{'='*70}\n")
        
        return full_doc
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [DOCUMENTATION] Critical error in parallel documentation workflow:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        
        # Return document indicating critical error
        error_doc = doc_header
        error_doc += f"## Critical Error in Generation\n\n"
        error_doc += f"A critical error occurred in the parallel documentation orchestrator:\n\n"
        error_doc += f"```\n{str(e)}\n```\n\n"
        error_doc += f"### Technical Details\n\n"
        error_doc += f"```\n{error_trace}\n```\n"
        
        return error_doc

def explain_file_direct(file_path: str, file_content: str) -> str:
    prompt = f"Explain in a short paragraph and 3 bullet points exactly what this code file does, its critical dependencies, and if it has any latent anti-patterns.\n\nFile: {file_path}\nContent:\n{file_content}"
    response = writer_llm.invoke(prompt)
    return response




