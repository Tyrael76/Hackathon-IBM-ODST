# Context Window Protection & Intelligent Chunking

## 🎯 Overview

This document describes the **Context Window Protection** mechanism implemented in `parser_core.py` to prevent LLM context window overflow when processing large repositories.

## 🚨 Problem Statement

When analyzing large repositories (5000+ files), the generated JSON output (`para_uriel.json`) can exceed safe context window limits for LLMs, causing:
- Token limit errors
- Incomplete analysis
- Memory issues
- Poor AI Agent performance

## ✅ Solution

An intelligent chunking system that:
1. **Estimates JSON size** before writing (character-based proxy for tokens)
2. **Automatically splits** large outputs into manageable chunks
3. **Adds metadata** to help AI Agents understand the fragmented architecture
4. **Maintains file integrity** - files are never split, only grouped differently

## 🔧 Key Features

### 1. Size Estimation
```python
estimate_json_size(data: Dict[str, Any]) -> int
```
- Serializes dictionary to JSON string
- Counts characters as token proxy
- Fast and accurate estimation

### 2. Intelligent Chunking
```python
chunk_repository_data(
    repository_data: Dict[str, Any],
    repository: str,
    max_chunk_size: int = 100000
) -> List[Tuple[Dict[str, Any], str]]
```
- Default limit: **100,000 characters** (~25,000 tokens for most LLMs)
- Splits data when exceeding limit
- Preserves file boundaries (never splits individual files)
- Sorts files for consistent chunking

### 3. Metadata Generation
```python
create_chunk_metadata(
    chunk_index: int,
    total_chunks: int,
    repository: str,
    chunk_file_count: int,
    total_file_count: int,
    chunk_size_chars: int
) -> Dict[str, Any]
```

Each chunk includes:
- Current chunk number and total chunks
- Repository identifier
- Generation timestamp
- File counts (chunk and total)
- Size information
- **Instructions for AI Agents** on how to load all parts

## 📊 Output Structure

### Single File (No Chunking)
```json
{
  "_metadata": {
    "chunk_info": {
      "current_chunk": 1,
      "total_chunks": 1,
      "is_fragmented": false
    },
    "repository": "user/repo",
    "generation_timestamp": "2026-05-16T00:00:00.000Z",
    "files_in_chunk": 150,
    "total_files_in_repository": 150,
    "chunk_size_characters": 85000,
    "instructions_for_ai": "Complete repository in single file."
  },
  "files": {
    "src/app.py": { ... },
    "src/utils.py": { ... }
  }
}
```

### Multiple Files (Chunked)
**para_uriel_part1.json:**
```json
{
  "_metadata": {
    "chunk_info": {
      "current_chunk": 1,
      "total_chunks": 3,
      "is_fragmented": true
    },
    "repository": "user/large-repo",
    "generation_timestamp": "2026-05-16T00:00:00.000Z",
    "files_in_chunk": 50,
    "total_files_in_repository": 150,
    "chunk_size_characters": 98500,
    "instructions_for_ai": "This is part 1 of 3. Load all parts (para_uriel_part1.json to para_uriel_part3.json) to get the complete repository analysis."
  },
  "files": {
    "src/module_a/file1.py": { ... },
    "src/module_a/file2.py": { ... }
  }
}
```

**para_uriel_part2.json, para_uriel_part3.json:** Similar structure with updated metadata

## 🎮 Usage

### Basic Usage (Default Settings)
```python
from parser_core import orchestrate_pipeline

result = orchestrate_pipeline(
    repository="user/repo",
    github_token="ghp_token",
    output_file="para_uriel.json"
)
# Automatically chunks if size > 100K chars
```

### Custom Chunk Size
```python
result = orchestrate_pipeline(
    repository="user/large-repo",
    github_token="ghp_token",
    output_file="para_uriel.json",
    max_chunk_size=50000  # 50K chars per chunk
)
```

### Disable Chunking
```python
result = orchestrate_pipeline(
    repository="user/repo",
    github_token="ghp_token",
    output_file="para_uriel.json",
    enable_chunking=False  # Force single file
)
```

## 📈 Performance Characteristics

### Test Results (from test_chunking_standalone.py)

**Test 1: Small Repository (5 files)**
- Input size: 2,051 chars
- Output: 1 file (para_uriel.json)
- Result: ✅ PASS

**Test 2: Large Repository (200 files)**
- Input size: 462,971 chars
- Chunk limit: 50,000 chars
- Output: 10 files (para_uriel_part1.json to para_uriel_part10.json)
- Chunk sizes: 48,958 - 49,068 chars (balanced distribution)
- Result: ✅ PASS

**Test 3: File Writing (100 files)**
- Input size: 181,271 chars
- Output: 4 files successfully written and validated
- Result: ✅ PASS

### Chunking Algorithm Efficiency
- **Time Complexity**: O(n) where n = number of files
- **Space Complexity**: O(n) for storing chunks
- **Overhead**: ~500 chars per chunk for metadata

## 🤖 AI Agent Integration Guide

### For Single File Output
```python
import json

with open("para_uriel.json", "r", encoding="utf-8") as f:
    data = json.load(f)

metadata = data["_metadata"]
files = data["files"]

if not metadata["chunk_info"]["is_fragmented"]:
    # Process all files at once
    analyze_repository(files)
```

### For Chunked Output
```python
import json
import glob

# Load all chunks
chunks = []
for chunk_file in sorted(glob.glob("para_uriel_part*.json")):
    with open(chunk_file, "r", encoding="utf-8") as f:
        chunks.append(json.load(f))

# Verify completeness
first_chunk = chunks[0]
total_chunks = first_chunk["_metadata"]["chunk_info"]["total_chunks"]
assert len(chunks) == total_chunks, "Missing chunks!"

# Merge all files
all_files = {}
for chunk in chunks:
    all_files.update(chunk["files"])

# Process complete repository
analyze_repository(all_files)
```

## 🔒 Safety Guarantees

1. **No File Splitting**: Individual files are never split across chunks
2. **Consistent Ordering**: Files are sorted alphabetically for reproducible chunking
3. **Metadata Integrity**: Each chunk knows its position in the sequence
4. **Size Validation**: Chunks stay within configured limits (with small tolerance for metadata)
5. **Error Handling**: Graceful fallback if chunking fails

## 🎯 Configuration Constants

```python
DEFAULT_CHUNK_SIZE = 100000  # 100K characters
METADATA_OVERHEAD = 500      # Reserved space per chunk
```

### Recommended Limits by LLM

| LLM Model | Context Window | Recommended Chunk Size |
|-----------|----------------|------------------------|
| GPT-4 | 8K tokens | 30,000 chars |
| GPT-4 Turbo | 128K tokens | 100,000 chars (default) |
| Claude 3 | 200K tokens | 150,000 chars |
| Gemini Pro | 32K tokens | 80,000 chars |

## 🧪 Testing

Run the standalone test suite:
```bash
python agents/compression_path/test_chunking_standalone.py
```

Expected output:
```
======================================================================
CONTEXT WINDOW PROTECTION - TEST SUITE
======================================================================
PASS - Small Data
PASS - Large Data
PASS - File Writing
======================================================================
Total: 3/3 tests passed (100.0%)
======================================================================
```

## 📝 Console Output Examples

### No Chunking Required
```
💾 [EXPORTACIÓN] Guardando resultados consolidados...
   📊 Tamaño estimado del JSON: 85,432 caracteres
   ✅ Tamaño dentro del límite seguro
   ✅ Guardado: para_uriel.json

🛡️ Protección de Ventana de Contexto:
   📏 Tamaño Total del JSON:              85,432 chars
   🎯 Límite Seguro Configurado:         100,000 chars
   ✅ Chunking Aplicado:                        NO

📁 Entregable generado para Uriel/IA: 'para_uriel.json'
```

### Chunking Applied
```
💾 [EXPORTACIÓN] Guardando resultados consolidados...
   📊 Tamaño estimado del JSON: 462,971 caracteres
   ⚠️ Tamaño excede el límite seguro (100,000 chars)
   🔪 Aplicando chunking inteligente...

⚠️ [CHUNKING] JSON size (462,971 chars) exceeds limit (100,000 chars)
   📦 Splitting into approximately 5 chunks...
   ✅ Successfully created 5 chunks

   ✅ Guardado: para_uriel_part1.json (98,500 chars, 42 archivos)
   ✅ Guardado: para_uriel_part2.json (99,200 chars, 43 archivos)
   ✅ Guardado: para_uriel_part3.json (98,800 chars, 42 archivos)
   ✅ Guardado: para_uriel_part4.json (99,100 chars, 43 archivos)
   ✅ Guardado: para_uriel_part5.json (67,371 chars, 30 archivos)

   📦 Total de archivos generados: 5

🛡️ Protección de Ventana de Contexto:
   📏 Tamaño Total del JSON:             462,971 chars
   🎯 Límite Seguro Configurado:         100,000 chars
   ⚠️ Chunking Aplicado:                        SÍ
   📦 Archivos Generados:                        5

📁 Entregables generados para Uriel/IA:
   1. para_uriel_part1.json
   2. para_uriel_part2.json
   3. para_uriel_part3.json
   4. para_uriel_part4.json
   5. para_uriel_part5.json
```

## 🚀 Future Enhancements

Potential improvements for future versions:

1. **Token-based estimation** using tiktoken library
2. **Compression** using gzip for storage efficiency
3. **Streaming API** for processing chunks without loading all in memory
4. **Smart file grouping** by module/package structure
5. **Parallel chunk processing** for faster analysis
6. **Chunk caching** to avoid re-processing unchanged files

## 📚 Related Documentation

- [CONCURRENT_ARCHITECTURE.md](./CONCURRENT_ARCHITECTURE.md) - Parallel processing details
- [OPTIMIZATION_NOTES.md](./OPTIMIZATION_NOTES.md) - Performance optimization strategies
- [parser_core.py](./parser_core.py) - Main implementation

## 👥 Credits

Implemented by: Bob (AI Software Engineer)
Date: 2026-05-16
Version: 1.0.0