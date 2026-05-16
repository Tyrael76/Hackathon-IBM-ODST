import ast
import json
from typing import Optional, Dict, List, Any

class StructuralAnalyzer(ast.NodeVisitor):
    """Optimized AST visitor for extracting Python code structure with minimal memory footprint."""
    
    __slots__ = ('_classes', '_global_functions', '_current_class', '_class_stack')
    
    def __init__(self):
        # Use __slots__ to reduce memory overhead per instance
        # Store classes as dict for O(1) lookup
        self._classes: Dict[str, Dict[str, Any]] = {}
        self._global_functions: List[Dict[str, Any]] = []
        
        # Use a stack for nested class support (more memory efficient than recursion)
        self._class_stack: List[Optional[str]] = []
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Triggered when a class definition is found."""
        class_name = node.name
        
        # Only get docstring if it exists (avoid creating default strings)
        docstring = ast.get_docstring(node)
        
        # Store the previous context to support nested classes
        self._class_stack.append(self._current_class)
        self._current_class = class_name
        
        # Use generator expression for lazy evaluation of inheritance
        # Only materialize when needed
        inheritance = [
            base.id for base in node.bases
            if isinstance(base, ast.Name)
        ]
        
        # Initialize the class entry with minimal data
        # Only store non-empty values to save memory
        class_data: Dict[str, Any] = {"methods": []}
        
        if inheritance:
            class_data["inheritance"] = inheritance
        
        if docstring:
            class_data["description"] = docstring
        
        self._classes[class_name] = class_data
        
        # Continue traversing nodes inside the class (controlled recursion)
        self.generic_visit(node)
        
        # Restore the previous context after leaving the class
        self._current_class = self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Triggered when a standard function definition is found."""
        self._extract_function_info(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Triggered when an asynchronous function definition is found."""
        self._extract_function_info(node)

    def _extract_function_info(self, node) -> None:
        """Shared logic for extracting function metadata with minimal allocations."""
        # Use tuple comprehension for immutable, memory-efficient storage
        args = tuple(arg.arg for arg in node.args.args)
        
        # Only get docstring if it exists
        docstring = ast.get_docstring(node)
        
        # Build function data incrementally to avoid unnecessary allocations
        function_data: Dict[str, Any] = {"name": node.name}
        
        if args:
            function_data["arguments"] = list(args)  # Convert to list only if needed
        
        if docstring:
            function_data["purpose"] = docstring
        
        # If a class context exists, treat it as a method; otherwise, as a global function
        if self._current_class:
            self._classes[self._current_class]["methods"].append(function_data)
        else:
            self._global_functions.append(function_data)
    
    def get_result(self) -> Dict[str, Any]:
        """Return the final repository structure, only including non-empty sections."""
        result = {}
        
        if self._classes:
            result["classes"] = self._classes
        
        if self._global_functions:
            result["global_functions"] = self._global_functions
        
        return result

def compress_python_code(source_code: str) -> Dict[str, Any]:
    """
    Parse Python source code and extract its structural information.
    
    Args:
        source_code: Python source code as a string
        
    Returns:
        Dictionary containing classes and global functions structure
    """
    try:
        tree = ast.parse(source_code)
        visitor = StructuralAnalyzer()
        visitor.visit(tree)
        return visitor.get_result()
    
    except SyntaxError:
        return {
            "error": "The file contains syntax errors and could not be analyzed."
        }

# Usage example
if __name__ == "__main__":
    code = """
class ImageProcessor:
    '''Class used to segment objects within a pipeline.'''
    
    def configure(self, threshold=127):
        pass

def initialize_system():
    pass
"""

    result = compress_python_code(code)
    print(json.dumps(result, indent=4))