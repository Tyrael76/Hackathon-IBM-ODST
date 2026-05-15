"""
Example for Antonio - Step 3: AST Compression
Demonstrates how to use fetch_github_repo_tool to receive files from Andre
and process them with AST before passing to Uriel.
"""

from fetch_github_repo_tool import fetch_github_repo_tool
import json
import ast

def compress_with_ast(source_code, path):
    """
    Example function to compress code using AST.
    Antonio should replace this with his actual compression logic.
    """
    try:
        # Try to parse as Python
        if path.endswith('.py'):
            tree = ast.parse(source_code)
            
            # Example: Extract information from AST
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            return {
                'compressed': True,
                'type': 'python',
                'functions': functions,
                'classes': classes,
                'ast_dump': ast.dump(tree)[:200] + '...',  # First 200 chars
                'size_original': len(source_code)
            }
        else:
            # For other files, use simple compression
            return {
                'compressed': True,
                'type': 'text',
                'size_original': len(source_code),
                'preview': source_code[:100] + '...'
            }
    except Exception as e:
        return {
            'compressed': False,
            'error': str(e),
            'size_original': len(source_code)
        }


def main():
    print("=" * 80)
    print("🔧 ANTONIO EXAMPLE - STEP 3: AST COMPRESSION")
    print("=" * 80)
    print()
    
    # Configuration
    GITHUB_TOKEN = "ghp_xxxxxxxxxxxxx"  # Replace with real token
    REPOSITORY = "user/repository"       # Replace with real repo
    
    print("📥 Step 1: Receive files from Andre (Step 2)")
    print(f"   Repository: {REPOSITORY}")
    print(f"   Token: {GITHUB_TOKEN[:10]}...")
    print()
    
    # Call Andre's tool
    result = fetch_github_repo_tool(
        repository=REPOSITORY,
        github_token=GITHUB_TOKEN,
        extensions=None  # Automatic intelligent filtering
    )
    
    # Check result
    if result['status'] != 'success':
        print(f"❌ Error: {result['message']}")
        return
    
    print(f"✅ {result['file_count']} files received from Andre")
    print()
    
    # Step 2: Compress with AST
    print("🔄 Step 2: Compressing files with AST...")
    print()
    
    compressed_files = []
    
    for i, file in enumerate(result['files'], 1):
        print(f"   [{i}/{result['file_count']}] Processing: {file['path']}")
        
        # Compress with AST
        compressed = compress_with_ast(file['content'], file['path'])
        
        # Save result
        compressed_files.append({
            'path': file['path'],
            'size_original': file['size'],
            'dependencies': file['dependencies'],
            'compressed_data': compressed
        })
    
    print()
    print(f"✅ {len(compressed_files)} files compressed")
    print()
    
    # Step 3: Save for Uriel (Step 4)
    output_file = 'files_for_uriel.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'repository': REPOSITORY,
            'total_files': len(compressed_files),
            'files': compressed_files
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📤 Step 3: File saved for Uriel")
    print(f"   File: {output_file}")
    print()
    
    # Show statistics
    print("📊 Statistics:")
    total_original = sum(f['size_original'] for f in compressed_files)
    python_files = sum(1 for f in compressed_files if f['path'].endswith('.py'))
    
    print(f"   - Total files: {len(compressed_files)}")
    print(f"   - Python files: {python_files}")
    print(f"   - Total size: {total_original / 1024:.2f} KB")
    print()
    
    # Show example of compressed file
    if compressed_files:
        print("📄 Example of compressed file:")
        example = compressed_files[0]
        print(f"   Path: {example['path']}")
        print(f"   Original size: {example['size_original']} bytes")
        print(f"   Dependencies: {example['dependencies']}")
        print(f"   Compressed: {example['compressed_data']['compressed']}")
        print()
    
    print("=" * 80)
    print("✅ PROCESS COMPLETE")
    print("=" * 80)
    print()
    print("📋 Next steps:")
    print("   1. ✅ Andre extracted repository (Step 2)")
    print("   2. ✅ Antonio compressed with AST (Step 3)")
    print("   3. ⏭️  Uriel will analyze with IBM Bob (Step 4)")
    print("   4. ⏭️  Gio will format to Markdown (Step 5)")
    print("   5. ⏭️  Rafiki will show to user (Frontend)")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
