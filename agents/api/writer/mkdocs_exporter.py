"""
MkDocs Project Exporter

This module exports documentation from the frontend JSON format to a complete
MkDocs project structure with Material theme configuration.
"""

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional


def export_mkdocs_project(
    frontend_docs: dict,
    base_output_dir: str = "generated_exports"
) -> dict:
    """
    Export frontend documentation JSON to a complete MkDocs project.
    
    Args:
        frontend_docs: Dictionary containing the frontend documentation structure
        base_output_dir: Base directory for generated exports
        
    Returns:
        Dictionary with export results including paths and status
    """
    # Validate input structure first
    is_valid, error_message = validate_frontend_docs(frontend_docs)
    if not is_valid:
        return {
            "mkdocs_available": False,
            "error": error_message
        }
    
    try:
        # Extract project information
        project_name = frontend_docs.get("project_name", "documentation")
        pages = frontend_docs.get("pages", [])
        
        # Create output directories
        base_path = Path(base_output_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        project_dir_name = f"{project_name}-mkdocs"
        project_path = base_path / project_dir_name
        docs_path = project_path / "docs"
        
        # Clean up existing directory if it exists
        if project_path.exists():
            shutil.rmtree(project_path)
        
        # Create project structure
        project_path.mkdir(parents=True, exist_ok=True)
        docs_path.mkdir(parents=True, exist_ok=True)
        
        # Sort pages by order
        sorted_pages = sorted(pages, key=lambda p: p.get("order", 999))
        
        # Generate markdown files
        files_generated = 0
        nav_items = []
        
        for page in sorted_pages:
            title = page.get("title", "Untitled")
            slug = page.get("slug", "page")
            markdown_content = page.get("markdown", "")
            
            # Handle overview -> index.md mapping
            if slug == "overview":
                filename = "index.md"
            else:
                filename = f"{slug}.md"
            
            # Write markdown file
            file_path = docs_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            files_generated += 1
            
            # Add to navigation
            nav_items.append({
                "title": title,
                "file": filename
            })
        
        # Generate mkdocs.yml
        mkdocs_config = _generate_mkdocs_config(project_name, nav_items)
        mkdocs_path = project_path / "mkdocs.yml"
        
        with open(mkdocs_path, "w", encoding="utf-8") as f:
            f.write(mkdocs_config)
        
        files_generated += 1
        
        # Create ZIP file
        zip_filename = f"{project_dir_name}.zip"
        zip_path = base_path / zip_filename
        
        _create_zip_archive(project_path, zip_path)
        
        # Return success result
        return {
            "mkdocs_available": True,
            "project_dir": str(project_path.absolute()),
            "zip_path": str(zip_path.absolute()),
            "files_generated": files_generated
        }
        
    except Exception as e:
        return {
            "mkdocs_available": False,
            "error": str(e)
        }


def _generate_mkdocs_config(project_name: str, nav_items: List[Dict]) -> str:
    """
    Generate mkdocs.yml configuration file content.
    
    Args:
        project_name: Name of the project
        nav_items: List of navigation items with title and file
        
    Returns:
        String containing the complete mkdocs.yml content
    """
    # Start with basic configuration
    config_lines = [
        f"site_name: {project_name}",
        "",
        "theme:",
        "  name: material",
        "  language: es",
        "",
        "markdown_extensions:",
        "  - tables",
        "  - fenced_code",
        "  - toc:",
        "      permalink: true",
        "",
        "nav:",
    ]
    
    # Add navigation items
    for item in nav_items:
        title = item["title"]
        file = item["file"]
        config_lines.append(f"  - {title}: {file}")
    
    return "\n".join(config_lines) + "\n"


def _create_zip_archive(source_dir: Path, zip_path: Path) -> None:
    """
    Create a ZIP archive of the MkDocs project.
    
    Args:
        source_dir: Path to the source directory to zip
        zip_path: Path where the ZIP file should be created
    """
    # Remove existing zip if it exists
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files in the source directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                # Calculate relative path for the archive
                arcname = file_path.relative_to(source_dir.parent)
                zipf.write(file_path, arcname)


def validate_frontend_docs(frontend_docs: dict) -> tuple[bool, Optional[str]]:
    """
    Validate the frontend documentation structure.
    
    Args:
        frontend_docs: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(frontend_docs, dict):
        return False, "frontend_docs must be a dictionary"
    
    if "pages" not in frontend_docs:
        return False, "Missing 'pages' field"
    
    pages = frontend_docs.get("pages", [])
    if not isinstance(pages, list):
        return False, "'pages' must be a list"
    
    if not pages:
        return False, "No pages found in documentation"
    
    # Validate each page has required fields
    for idx, page in enumerate(pages):
        if not isinstance(page, dict):
            return False, f"Page {idx} is not a dictionary"
        
        if "slug" not in page:
            return False, f"Page {idx} missing 'slug' field"
        
        if "markdown" not in page:
            return False, f"Page {idx} missing 'markdown' field"
    
    return True, None


def get_export_info(frontend_docs: dict, base_output_dir: str = "generated_exports") -> dict:
    """
    Get information about what would be exported without actually exporting.
    
    Args:
        frontend_docs: Dictionary containing the frontend documentation structure
        base_output_dir: Base directory for generated exports
        
    Returns:
        Dictionary with export information
    """
    project_name = frontend_docs.get("project_name", "documentation")
    pages = frontend_docs.get("pages", [])
    
    project_dir_name = f"{project_name}-mkdocs"
    base_path = Path(base_output_dir)
    project_path = base_path / project_dir_name
    zip_path = base_path / f"{project_dir_name}.zip"
    
    return {
        "project_name": project_name,
        "page_count": len(pages),
        "project_dir": str(project_path.absolute()),
        "zip_path": str(zip_path.absolute()),
        "estimated_files": len(pages) + 1  # pages + mkdocs.yml
    }


if __name__ == "__main__":
    # Example usage for testing
    sample_docs = {
        "project_name": "task-manager-api",
        "documentation_format": "markdown",
        "generated_at": "2026-05-15T00:00:00Z",
        "pages": [
            {
                "title": "Inicio",
                "slug": "overview",
                "order": 1,
                "markdown": "# Inicio\n\nBienvenido a la documentación."
            },
            {
                "title": "Arquitectura",
                "slug": "architecture",
                "order": 2,
                "markdown": "# Arquitectura\n\nDescripción de la arquitectura."
            },
            {
                "title": "Configuración",
                "slug": "setup",
                "order": 3,
                "markdown": "# Configuración\n\nGuía de configuración."
            }
        ],
        "exports": {
            "mkdocs_available": False,
            "download_url": None
        }
    }
    
    # Validate
    is_valid, error = validate_frontend_docs(sample_docs)
    if not is_valid:
        print(f"Validation error: {error}")
    else:
        print("Documentation structure is valid")
        
        # Get export info
        info = get_export_info(sample_docs)
        print(f"\nExport info:")
        print(json.dumps(info, indent=2))
        
        # Export
        result = export_mkdocs_project(sample_docs)
        print(f"\nExport result:")
        print(json.dumps(result, indent=2))

# Made with Bob
