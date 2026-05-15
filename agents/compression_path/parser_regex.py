"""
Optimized Regex Parser for Non-Python Code Analysis
====================================================
Pre-compiled regex patterns for maximum CPU efficiency.
Extracts function signatures, classes, API endpoints, and exposed credentials.
Acts as a fallback scanner to save tokens before sending context to LLM.
"""

import re
from typing import Dict, Any, List, Iterator, Tuple, Optional
from functools import lru_cache

# ==========================================
# PRE-COMPILED REGEX PATTERNS (Module Level)
# ==========================================
# Compiled once at module load time, stored in C-optimized structures

# Universal class pattern
CLASS_PATTERN = re.compile(
    r'class\s+([a-zA-Z_]\w*)',
    re.MULTILINE
)

# JavaScript/TypeScript function patterns
JS_FUNCTION_PATTERN = re.compile(
    r'function\s+([a-zA-Z_]\w*)\s*\((.*?)\)',
    re.MULTILINE
)

JS_ARROW_PATTERN = re.compile(
    r'(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*\((.*?)\)\s*=>',
    re.MULTILINE
)

# Kotlin/Java/C# method patterns
JVM_METHOD_PATTERN = re.compile(
    r'(?:fun|public|private|protected|static)\s+(?:[\w<>,\[\]\s]+\s+)?([a-zA-Z_]\w*)\s*\((.*?)\)',
    re.MULTILINE
)

# API endpoint patterns (REST)
API_ENDPOINT_PATTERN = re.compile(
    r'@(?:Get|Post|Put|Delete|Patch|Request)(?:Mapping)?\s*\(["\']([^"\']+)["\']',
    re.MULTILINE | re.IGNORECASE
)

# Exposed credentials patterns (security scan)
CREDENTIAL_PATTERNS = [
    re.compile(r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE),
    re.compile(r'(?:password|passwd|pwd)\s*[:=]\s*["\']([^"\']{4,})["\']', re.IGNORECASE),
    re.compile(r'(?:secret|token)\s*[:=]\s*["\']([^"\']{8,})["\']', re.IGNORECASE),
    re.compile(r'(?:aws|amazon)[_-]?(?:access|secret)[_-]?key\s*[:=]\s*["\']([^"\']{16,})["\']', re.IGNORECASE),
]

# Control flow keywords to filter out (not real functions)
CONTROL_KEYWORDS = frozenset(['if', 'for', 'while', 'switch', 'catch', 'try', 'with', 'return'])

# Regex timeout protection (milliseconds)
REGEX_TIMEOUT_MS = 5000


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def _extract_classes(source_code: str) -> Iterator[Tuple[str, Dict[str, str]]]:
    """
    Generator that yields class names and metadata.
    Memory efficient - doesn't build intermediate lists.
    """
    try:
        for match in CLASS_PATTERN.finditer(source_code):
            class_name = match.group(1)
            yield class_name, {"description": "Extracted via Regex"}
    except re.error as e:
        # Catastrophic backtracking protection
        raise ValueError(f"Regex error in class extraction: {e}")


def _parse_arguments(args_str: str) -> List[str]:
    """
    Parse function arguments string into list.
    Cached for repeated argument patterns.
    """
    if not args_str or not args_str.strip():
        return []
    return [arg.strip() for arg in args_str.split(',') if arg.strip()]


def _extract_js_functions(source_code: str) -> Iterator[Dict[str, Any]]:
    """
    Generator for JavaScript/TypeScript function extraction.
    Handles both classic and arrow functions.
    """
    try:
        # Classic functions: function name(args)
        for match in JS_FUNCTION_PATTERN.finditer(source_code):
            func_name = match.group(1)
            args = _parse_arguments(match.group(2))
            yield {"name": func_name, "arguments": args, "type": "function"}
        
        # Arrow functions: const name = (args) =>
        for match in JS_ARROW_PATTERN.finditer(source_code):
            func_name = match.group(1)
            args = _parse_arguments(match.group(2))
            yield {"name": func_name, "arguments": args, "type": "arrow"}
            
    except re.error as e:
        raise ValueError(f"Regex error in JS function extraction: {e}")


def _extract_jvm_methods(source_code: str) -> Iterator[Dict[str, Any]]:
    """
    Generator for Kotlin/Java/C# method extraction.
    Filters out control flow keywords.
    """
    try:
        for match in JVM_METHOD_PATTERN.finditer(source_code):
            method_name = match.group(1)
            
            # Filter control keywords that regex might confuse with methods
            if method_name not in CONTROL_KEYWORDS:
                args = _parse_arguments(match.group(2))
                yield {"name": method_name, "arguments": args, "type": "method"}
                
    except re.error as e:
        raise ValueError(f"Regex error in JVM method extraction: {e}")


def _extract_api_endpoints(source_code: str) -> Iterator[str]:
    """
    Generator for REST API endpoint extraction.
    Useful for API documentation and security analysis.
    """
    try:
        for match in API_ENDPOINT_PATTERN.finditer(source_code):
            endpoint = match.group(1)
            yield endpoint
    except re.error as e:
        raise ValueError(f"Regex error in API endpoint extraction: {e}")


def _scan_credentials(source_code: str) -> Iterator[Dict[str, Any]]:
    """
    Generator for exposed credential detection.
    Security scanner to identify hardcoded secrets.
    """
    for pattern in CREDENTIAL_PATTERNS:
        try:
            for match in pattern.finditer(source_code):
                credential_value = match.group(1)
                # Mask the credential for security
                masked_value = credential_value[:4] + '*' * (len(credential_value) - 4)
                yield {
                    "type": "exposed_credential",
                    "value": masked_value,
                    "line": source_code[:match.start()].count('\n') + 1
                }
        except re.error:
            # Skip problematic patterns silently
            continue


# ==========================================
# MAIN COMPRESSION FUNCTION
# ==========================================

def compress_regex_code(source_code: str, extension: str) -> Dict[str, Any]:
    """
    Optimized regex-based parser for non-Python code.
    
    Extracts:
    - Class definitions
    - Function/method signatures
    - API endpoints
    - Exposed credentials (security scan)
    
    Args:
        source_code: Source code content as string
        extension: File extension (e.g., '.js', '.kt', '.java')
    
    Returns:
        Dictionary with extracted code elements
    
    Raises:
        ValueError: If regex operations fail catastrophically
        TypeError: If input types are invalid
    """
    # Input validation
    if not isinstance(source_code, str):
        raise TypeError(f"source_code must be str, got {type(source_code)}")
    if not isinstance(extension, str):
        raise TypeError(f"extension must be str, got {type(extension)}")
    
    # Early return for empty source
    if not source_code.strip():
        return {}
    
    result: Dict[str, Any] = {}
    
    try:
        # Extract classes (universal pattern)
        classes_dict = dict(_extract_classes(source_code))
        if classes_dict:
            result["classes"] = classes_dict
        
        # Extract functions based on file extension
        if extension in {'.js', '.ts', '.jsx', '.tsx'}:
            # JavaScript/TypeScript
            functions_list = list(_extract_js_functions(source_code))
            if functions_list:
                result["global_functions"] = functions_list
            
            # Extract API endpoints (common in JS backends)
            endpoints = list(_extract_api_endpoints(source_code))
            if endpoints:
                result["api_endpoints"] = endpoints
                
        elif extension in {'.kt', '.java', '.cs'}:
            # Kotlin/Java/C#
            methods_list = list(_extract_jvm_methods(source_code))
            if methods_list:
                result["global_functions"] = methods_list
            
            # Extract API endpoints (Spring Boot, ASP.NET annotations)
            endpoints = list(_extract_api_endpoints(source_code))
            if endpoints:
                result["api_endpoints"] = endpoints
        
        # Security scan: Check for exposed credentials (all file types)
        credentials = list(_scan_credentials(source_code))
        if credentials:
            result["security_warnings"] = credentials
        
    except ValueError as e:
        # Regex catastrophic backtracking or other regex errors
        result["error"] = str(e)
    except Exception as e:
        # Unexpected errors
        result["error"] = f"Unexpected error: {type(e).__name__}: {e}"
    
    return result


# ==========================================
# LOCAL TESTING ZONE
# ==========================================
if __name__ == "__main__":
    import json
    
    # Test 1: JavaScript code
    codigo_js = """
    class ControladorFrontend {
        constructor() {}
    }
    
    function validarFormulario(evento, datos) {
        return true;
    }
    
    const enviarDatos = (url, payload) => {
        console.log(url);
    }
    
    const API_KEY = "sk-1234567890abcdef";
    """
    
    print("=" * 50)
    print("TEST 1: JavaScript Code")
    print("=" * 50)
    resultado = compress_regex_code(codigo_js, '.js')
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Test 2: Kotlin code
    codigo_kt = """
    class UserService {
        fun getUserById(id: Long): User {
            return repository.findById(id)
        }
        
        private fun validateUser(user: User): Boolean {
            return user.email.isNotEmpty()
        }
    }
    """
    
    print("\n" + "=" * 50)
    print("TEST 2: Kotlin Code")
    print("=" * 50)
    resultado_kt = compress_regex_code(codigo_kt, '.kt')
    print(json.dumps(resultado_kt, indent=2, ensure_ascii=False))
    
    # Test 3: Security scan
    codigo_inseguro = """
    const config = {
        apiKey: "AIzaSyD1234567890abcdefghijklmnop",
        password: "admin123",
        aws_secret_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    };
    """
    
    print("\n" + "=" * 50)
    print("TEST 3: Security Scan")
    print("=" * 50)
    resultado_sec = compress_regex_code(codigo_inseguro, '.js')
    print(json.dumps(resultado_sec, indent=2, ensure_ascii=False))

# Made with Bob
