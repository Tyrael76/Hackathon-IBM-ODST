"""
Test script for Context Window Protection and Chunking functionality
====================================================================
Validates the chunking mechanism without requiring GitHub API access.
"""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser_core import (
    estimate_json_size,
    create_chunk_metadata,
    chunk_repository_data,
    DEFAULT_CHUNK_SIZE
)


def generate_mock_repository_data(num_files: int = 100, file_size: int = 1000) -> dict:
    """Generate mock repository data for testing."""
    mock_data = {}
    
    for i in range(num_files):
        file_path = f"src/module_{i // 10}/file_{i}.py"
        mock_data[file_path] = {
            "language": "python",
            "external_imports": ["os", "sys", "json"],
            "structure": {
                "classes": [
                    {
                        "name": f"TestClass_{i}",
                        "methods": [
                            {"name": "method_1", "params": ["self", "arg1"]},
                            {"name": "method_2", "params": ["self", "arg2", "arg3"]}
                        ],
                        "docstring": "A" * file_size  # Padding to control size
                    }
                ],
                "functions": [
                    {"name": f"test_function_{i}", "params": ["param1", "param2"]}
                ]
            }
        }
    
    return mock_data


def test_estimate_json_size():
    """Test JSON size estimation."""
    print("\n" + "="*70)
    print("TEST 1: JSON Size Estimation")
    print("="*70)
    
    test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
    estimated_size = estimate_json_size(test_data)
    actual_size = len(json.dumps(test_data, ensure_ascii=False, separators=(',', ':')))
    
    print(f"Estimated size: {estimated_size} chars")
    print(f"Actual size:    {actual_size} chars")
    print(f"Match: {'✅ PASS' if estimated_size == actual_size else '❌ FAIL'}")
    
    return estimated_size == actual_size


def test_chunk_metadata():
    """Test metadata generation."""
    print("\n" + "="*70)
    print("TEST 2: Chunk Metadata Generation")
    print("="*70)
    
    metadata = create_chunk_metadata(
        chunk_index=1,
        total_chunks=3,
        repository="test/repo",
        chunk_file_count=50,
        total_file_count=150,
        chunk_size_chars=50000
    )
    
    print(f"Metadata structure:")
    print(json.dumps(metadata, indent=2))
    
    # Validate required fields
    required_fields = ["_metadata"]
    has_all_fields = all(field in metadata for field in required_fields)
    
    print(f"\nValidation: {'✅ PASS' if has_all_fields else '❌ FAIL'}")
    return has_all_fields


def test_chunking_small_data():
    """Test chunking with data that fits in one chunk."""
    print("\n" + "="*70)
    print("TEST 3: Small Data (No Chunking Required)")
    print("="*70)
    
    small_data = generate_mock_repository_data(num_files=5, file_size=100)
    data_size = estimate_json_size(small_data)
    
    print(f"Generated data size: {data_size:,} chars")
    print(f"Chunk limit: {DEFAULT_CHUNK_SIZE:,} chars")
    
    chunks = chunk_repository_data(small_data, "test/small-repo", DEFAULT_CHUNK_SIZE)
    
    print(f"Number of chunks created: {len(chunks)}")
    print(f"Expected: 1 chunk")
    
    success = len(chunks) == 1
    print(f"\nValidation: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        chunk_data, filename = chunks[0]
        print(f"Filename: {filename}")
        print(f"Has metadata: {'✅' if '_metadata' in chunk_data else '❌'}")
        print(f"Has files: {'✅' if 'files' in chunk_data else '❌'}")
    
    return success


def test_chunking_large_data():
    """Test chunking with data that requires splitting."""
    print("\n" + "="*70)
    print("TEST 4: Large Data (Chunking Required)")
    print("="*70)
    
    # Generate data larger than chunk limit
    large_data = generate_mock_repository_data(num_files=200, file_size=2000)
    data_size = estimate_json_size(large_data)
    
    print(f"Generated data size: {data_size:,} chars")
    
    # Use smaller chunk size for testing
    test_chunk_size = 50000
    print(f"Test chunk limit: {test_chunk_size:,} chars")
    
    chunks = chunk_repository_data(large_data, "test/large-repo", test_chunk_size)
    
    print(f"Number of chunks created: {len(chunks)}")
    
    success = len(chunks) > 1
    print(f"\nValidation: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\nChunk details:")
        for i, (chunk_data, filename) in enumerate(chunks, 1):
            chunk_size = estimate_json_size(chunk_data)
            files_count = len(chunk_data.get("files", {}))
            metadata = chunk_data.get("_metadata", {})
            chunk_info = metadata.get("chunk_info", {})
            
            print(f"  Chunk {i}:")
            print(f"    Filename: {filename}")
            print(f"    Size: {chunk_size:,} chars")
            print(f"    Files: {files_count}")
            print(f"    Current/Total: {chunk_info.get('current_chunk')}/{chunk_info.get('total_chunks')}")
            
            # Validate chunk doesn't exceed limit (with some tolerance for metadata)
            if chunk_size > test_chunk_size * 1.1:  # 10% tolerance
                print(f"    ⚠️ WARNING: Chunk exceeds limit!")
    
    return success


def test_chunk_file_writing():
    """Test actual file writing with chunking."""
    print("\n" + "="*70)
    print("TEST 5: File Writing with Chunking")
    print("="*70)
    
    test_data = generate_mock_repository_data(num_files=100, file_size=1500)
    test_chunk_size = 50000
    
    chunks = chunk_repository_data(test_data, "test/write-repo", test_chunk_size)
    
    print(f"Writing {len(chunks)} chunk(s) to disk...")
    
    written_files = []
    try:
        for chunk_data, filename in chunks:
            test_filename = f"test_{filename}"
            with open(test_filename, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(test_filename)
            written_files.append(test_filename)
            print(f"  ✅ Written: {test_filename} ({file_size:,} bytes)")
        
        print(f"\nValidation: ✅ PASS - All files written successfully")
        
        # Cleanup
        print("\nCleaning up test files...")
        for file in written_files:
            os.remove(file)
            print(f"  🗑️ Removed: {file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        # Cleanup on error
        for file in written_files:
            if os.path.exists(file):
                os.remove(file)
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("🧪 CONTEXT WINDOW PROTECTION - TEST SUITE")
    print("="*70)
    
    tests = [
        ("JSON Size Estimation", test_estimate_json_size),
        ("Chunk Metadata Generation", test_chunk_metadata),
        ("Small Data (No Chunking)", test_chunking_small_data),
        ("Large Data (Chunking)", test_chunking_large_data),
        ("File Writing", test_chunk_file_writing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Final report
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
