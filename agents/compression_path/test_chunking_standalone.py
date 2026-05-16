"""
Standalone Test for Context Window Protection and Chunking
===========================================================
Tests the chunking logic independently without full module imports.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple


# ==========================================
# COPIED FUNCTIONS FOR STANDALONE TESTING
# ==========================================

DEFAULT_CHUNK_SIZE = 100000
METADATA_OVERHEAD = 500


def estimate_json_size(data: Dict[str, Any]) -> int:
    """Estimate the size of a dictionary when serialized to JSON."""
    try:
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return len(json_str)
    except Exception as e:
        print(f"Warning: Error estimating JSON size: {e}")
        return len(str(data))


def create_chunk_metadata(
    chunk_index: int,
    total_chunks: int,
    repository: str,
    chunk_file_count: int,
    total_file_count: int,
    chunk_size_chars: int
) -> Dict[str, Any]:
    """Generate metadata for a chunked output file."""
    return {
        "_metadata": {
            "chunk_info": {
                "current_chunk": chunk_index,
                "total_chunks": total_chunks,
                "is_fragmented": total_chunks > 1
            },
            "repository": repository,
            "generation_timestamp": datetime.utcnow().isoformat() + "Z",
            "files_in_chunk": chunk_file_count,
            "total_files_in_repository": total_file_count,
            "chunk_size_characters": chunk_size_chars,
            "instructions_for_ai": (
                f"This is part {chunk_index} of {total_chunks}. "
                f"Load all parts (para_uriel_part1.json to para_uriel_part{total_chunks}.json) "
                "to get the complete repository analysis."
            ) if total_chunks > 1 else "Complete repository in single file."
        }
    }


def chunk_repository_data(
    repository_data: Dict[str, Any],
    repository: str,
    max_chunk_size: int = DEFAULT_CHUNK_SIZE
) -> List[Tuple[Dict[str, Any], str]]:
    """Split large repository data into manageable chunks with metadata."""
    total_size = estimate_json_size(repository_data)
    total_files = len(repository_data)
    
    if total_size <= max_chunk_size:
        chunk_with_metadata = {
            **create_chunk_metadata(1, 1, repository, total_files, total_files, total_size),
            "files": repository_data
        }
        return [(chunk_with_metadata, "para_uriel.json")]
    
    estimated_chunks = (total_size // max_chunk_size) + 1
    print(f"\nChunking: JSON size ({total_size:,} chars) exceeds limit ({max_chunk_size:,} chars)")
    print(f"Splitting into approximately {estimated_chunks} chunks...")
    
    chunks = []
    current_chunk = {}
    current_chunk_size = METADATA_OVERHEAD
    chunk_index = 1
    
    sorted_files = sorted(repository_data.items())
    
    for file_path, file_data in sorted_files:
        file_entry = {file_path: file_data}
        file_size = estimate_json_size(file_entry)
        
        if current_chunk and (current_chunk_size + file_size > max_chunk_size):
            chunk_with_metadata = {
                **create_chunk_metadata(
                    chunk_index, 0, repository,
                    len(current_chunk), total_files, current_chunk_size
                ),
                "files": current_chunk
            }
            chunks.append(chunk_with_metadata)
            
            current_chunk = {}
            current_chunk_size = METADATA_OVERHEAD
            chunk_index += 1
        
        current_chunk[file_path] = file_data
        current_chunk_size += file_size
    
    if current_chunk:
        chunk_with_metadata = {
            **create_chunk_metadata(
                chunk_index, 0, repository,
                len(current_chunk), total_files, current_chunk_size
            ),
            "files": current_chunk
        }
        chunks.append(chunk_with_metadata)
    
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        chunk["_metadata"]["chunk_info"]["total_chunks"] = total_chunks
        chunk["_metadata"]["chunk_info"]["current_chunk"] = i
        chunk["_metadata"]["instructions_for_ai"] = (
            f"This is part {i} of {total_chunks}. "
            f"Load all parts (para_uriel_part1.json to para_uriel_part{total_chunks}.json) "
            "to get the complete repository analysis."
        )
    
    result = []
    for i, chunk in enumerate(chunks, 1):
        filename = f"para_uriel_part{i}.json" if total_chunks > 1 else "para_uriel.json"
        result.append((chunk, filename))
    
    print(f"Successfully created {total_chunks} chunks")
    return result


# ==========================================
# TEST FUNCTIONS
# ==========================================

def generate_mock_data(num_files: int, file_size: int) -> dict:
    """Generate mock repository data."""
    mock_data = {}
    for i in range(num_files):
        file_path = f"src/module_{i // 10}/file_{i}.py"
        mock_data[file_path] = {
            "language": "python",
            "external_imports": ["os", "sys", "json"],
            "structure": {
                "classes": [{
                    "name": f"TestClass_{i}",
                    "methods": [
                        {"name": "method_1", "params": ["self", "arg1"]},
                        {"name": "method_2", "params": ["self", "arg2"]}
                    ],
                    "docstring": "A" * file_size
                }],
                "functions": [{"name": f"test_func_{i}", "params": ["p1", "p2"]}]
            }
        }
    return mock_data


def test_small_data():
    """Test with data that fits in one chunk."""
    print("\n" + "="*70)
    print("TEST 1: Small Data (No Chunking)")
    print("="*70)
    
    data = generate_mock_data(5, 100)
    size = estimate_json_size(data)
    print(f"Data size: {size:,} chars")
    
    chunks = chunk_repository_data(data, "test/small", DEFAULT_CHUNK_SIZE)
    
    success = len(chunks) == 1
    print(f"Chunks created: {len(chunks)}")
    print(f"Result: {'PASS' if success else 'FAIL'}")
    
    if success:
        chunk_data, filename = chunks[0]
        print(f"Filename: {filename}")
        print(f"Has metadata: {bool('_metadata' in chunk_data)}")
        print(f"Has files: {bool('files' in chunk_data)}")
    
    return success


def test_large_data():
    """Test with data that requires chunking."""
    print("\n" + "="*70)
    print("TEST 2: Large Data (Chunking Required)")
    print("="*70)
    
    data = generate_mock_data(200, 2000)
    size = estimate_json_size(data)
    print(f"Data size: {size:,} chars")
    
    test_limit = 50000
    chunks = chunk_repository_data(data, "test/large", test_limit)
    
    success = len(chunks) > 1
    print(f"Chunks created: {len(chunks)}")
    print(f"Result: {'PASS' if success else 'FAIL'}")
    
    if success:
        print("\nChunk details:")
        for i, (chunk_data, filename) in enumerate(chunks, 1):
            chunk_size = estimate_json_size(chunk_data)
            files_count = len(chunk_data.get("files", {}))
            print(f"  Chunk {i}: {filename} - {chunk_size:,} chars, {files_count} files")
    
    return success


def test_file_writing():
    """Test writing chunks to disk."""
    print("\n" + "="*70)
    print("TEST 3: File Writing")
    print("="*70)
    
    data = generate_mock_data(100, 1500)
    chunks = chunk_repository_data(data, "test/write", 50000)
    
    written_files = []
    try:
        for chunk_data, filename in chunks:
            test_file = f"test_{filename}"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            size = os.path.getsize(test_file)
            written_files.append(test_file)
            print(f"Written: {test_file} ({size:,} bytes)")
        
        print(f"Result: PASS - {len(written_files)} files written")
        
        # Cleanup
        for file in written_files:
            os.remove(file)
        
        return True
        
    except Exception as e:
        print(f"Result: FAIL - {e}")
        for file in written_files:
            if os.path.exists(file):
                os.remove(file)
        return False


def run_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("CONTEXT WINDOW PROTECTION - TEST SUITE")
    print("="*70)
    
    tests = [
        ("Small Data", test_small_data),
        ("Large Data", test_large_data),
        ("File Writing", test_file_writing)
    ]
    
    results = []
    for name, func in tests:
        try:
            result = func()
            results.append((name, result))
        except Exception as e:
            print(f"\nTest '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {name}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)

# Made with Bob
