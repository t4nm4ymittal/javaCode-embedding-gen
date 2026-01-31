# Java Code Chunking and ChromaDB Storage - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Detailed Component Guide](#detailed-component-guide)
6. [Configuration Options](#configuration-options)
7. [Use Cases](#use-cases)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

This project provides a complete solution for intelligently chunking Java source code and storing it in ChromaDB for semantic search and retrieval. It uses **tree-sitter** for Abstract Syntax Tree (AST) parsing to ensure code is split at meaningful boundaries.

### Why This Matters

Traditional text chunking splits code arbitrarily, often breaking:
- Methods in the middle
- Class definitions
- Logic flow

**Tree-based chunking** respects the structure of your code, creating chunks that:
- Are semantically meaningful
- Preserve context
- Enable better search and retrieval

### Key Features

✅ **AST-Based Parsing**: Uses tree-sitter to understand Java syntax  
✅ **Intelligent Splitting**: Respects class and method boundaries  
✅ **Configurable Chunk Sizes**: Adjust to your needs  
✅ **Overlap Support**: Maintains context between chunks  
✅ **Rich Metadata**: Tracks file paths, class names, method names  
✅ **Semantic Search**: Find code by meaning, not just keywords  
✅ **Persistent Storage**: ChromaDB stores everything on disk  

---

## Architecture

```
┌─────────────────┐
│  Java Files     │
│  (.java)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tree-Sitter    │ ◄─── Parses Java into AST
│  Parser         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JavaCodeChunker│ ◄─── Intelligently splits code
│                 │      • Respects boundaries
│  • chunk_code() │      • Adds metadata
│  • merge_small  │      • Handles overlap
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CodeChunk[]    │ ◄─── List of chunks with metadata
│                 │
│  • content      │
│  • start_line   │
│  • metadata     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ChromaDB       │ ◄─── Stores + generates embeddings
│  Manager        │
│                 │
│  • add_chunks() │      • Automatic embeddings
│  • search()     │      • Semantic search
└─────────────────┘      • Persistent storage
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install tree-sitter tree-sitter-java chromadb sentence-transformers
```

### Verify Installation

```python
import tree_sitter
import tree_sitter_java
import chromadb

print("✓ All dependencies installed successfully!")
```

---

## Quick Start

### 1. Basic Usage

```python
from java_code_chunker import JavaCodeChunker, ChromaDBManager

# Initialize chunker
chunker = JavaCodeChunker(
    max_chunk_size=1000,
    chunk_overlap=200
)

# Read Java code
with open('MyClass.java', 'r') as f:
    java_code = f.read()

# Chunk the code
chunks = chunker.chunk_code(java_code, file_path='MyClass.java')

# Initialize ChromaDB
db = ChromaDBManager(collection_name="my_java_code")

# Store chunks
db.add_chunks(chunks)

# Search
results = db.search("method to validate user input", n_results=5)
```

### 2. Process Entire Directory

```python
from pathlib import Path

# Process all Java files in a directory
java_files = Path('src/main/java').rglob('*.java')

all_chunks = []
for java_file in java_files:
    with open(java_file, 'r') as f:
        code = f.read()
    chunks = chunker.chunk_code(code, file_path=str(java_file))
    all_chunks.extend(chunks)

# Store all chunks
db.add_chunks(all_chunks)
```

---

## Detailed Component Guide

### JavaCodeChunker

The core class responsible for parsing and chunking Java code.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_chunk_size` | int | 1000 | Maximum characters per chunk |
| `chunk_overlap` | int | 200 | Overlapping characters between consecutive chunks |
| `min_chunk_size` | int | 100 | Minimum chunk size before merging with adjacent chunks |

#### Key Methods

**`chunk_code(code: str, file_path: str = "") -> List[CodeChunk]`**

Main method to chunk Java code.

**Process:**
1. Parses code into AST using tree-sitter
2. Identifies top-level structures (package, imports, classes)
3. Splits classes into methods and fields
4. Creates chunks with metadata
5. Merges small chunks
6. Adds overlap between chunks

**Parameters:**
- `code`: Java source code as string
- `file_path`: Optional file path for metadata

**Returns:** List of `CodeChunk` objects

**Example:**
```python
chunker = JavaCodeChunker(max_chunk_size=1500)
chunks = chunker.chunk_code(java_code, "src/User.java")

for chunk in chunks:
    print(f"{chunk.chunk_type}: lines {chunk.start_line}-{chunk.end_line}")
```

### CodeChunk Data Structure

Represents a single chunk of code with associated metadata.

```python
@dataclass
class CodeChunk:
    content: str          # The actual code text
    start_line: int       # Starting line number (1-indexed)
    end_line: int         # Ending line number (1-indexed)
    chunk_type: str       # Type of chunk
    metadata: Dict        # Additional information
```

#### Chunk Types

- `package`: Package declaration
- `import`: Import statement
- `class`: Class declaration (when not split further)
- `method`: Method or constructor
- `field`: Field declaration
- `class_member`: Other class members
- `comment`: Comments
- `merged`: Multiple small chunks merged together

#### Metadata Fields

Common metadata fields include:

```python
{
    'file_path': 'src/main/java/User.java',
    'class_name': 'UserManager',
    'method_name': 'addUser',
    'node_type': 'method_declaration',
    'length': 245,
    'has_overlap': True
}
```

### ChromaDBManager

Manages storage and retrieval of code chunks in ChromaDB.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection_name` | str | "java_code" | Name of the ChromaDB collection |
| `persist_directory` | str | "./chroma_db" | Directory for persistent storage |

#### Key Methods

**`add_chunks(chunks: List[CodeChunk], batch_size: int = 100)`**

Adds code chunks to ChromaDB.

**Process:**
1. Extracts content from each chunk
2. Prepares metadata (converts all values to strings)
3. Generates unique IDs
4. Adds to ChromaDB in batches (automatic embedding generation)

**Parameters:**
- `chunks`: List of CodeChunk objects
- `batch_size`: Number of chunks to add per batch

**Example:**
```python
db = ChromaDBManager(collection_name="my_code")
db.add_chunks(chunks, batch_size=50)
```

**`search(query: str, n_results: int = 5) -> Dict`**

Searches for similar code using semantic similarity.

**Parameters:**
- `query`: Search query (natural language or code snippet)
- `n_results`: Number of results to return

**Returns:** Dictionary with:
- `documents`: List of matching code chunks
- `metadatas`: List of metadata for each result
- `distances`: List of similarity distances (lower = more similar)

**Example:**
```python
results = db.search("method that validates email address", n_results=3)

for doc, meta, distance in zip(
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0]
):
    similarity = 1 - distance
    print(f"Similarity: {similarity:.2%}")
    print(f"File: {meta['file_path']}")
    print(f"Code:\n{doc}\n")
```

**`get_all_chunks() -> Dict`**

Retrieves all chunks from the collection.

**`delete_collection()`**

Deletes the entire collection.

---

## Configuration Options

### Chunking Strategy Configuration

```python
# Conservative: Small, focused chunks
chunker = JavaCodeChunker(
    max_chunk_size=500,   # Smaller chunks
    chunk_overlap=100,    # Less overlap
    min_chunk_size=50     # Keep smaller pieces
)

# Balanced: Good for most use cases
chunker = JavaCodeChunker(
    max_chunk_size=1000,
    chunk_overlap=200,
    min_chunk_size=100
)

# Aggressive: Larger, more contextual chunks
chunker = JavaCodeChunker(
    max_chunk_size=2000,  # Larger chunks
    chunk_overlap=400,    # More overlap
    min_chunk_size=200    # Merge more aggressively
)
```

### When to Use Each Strategy

**Small Chunks (500-800 chars):**
- Fine-grained code search
- Specific method or function lookup
- When you need precise matches
- Limited embedding model context window

**Medium Chunks (800-1500 chars):**
- General purpose code search
- Balanced context and precision
- Most RAG applications
- Good default choice

**Large Chunks (1500-3000 chars):**
- Need more context around code
- Working with complex classes
- Documentation generation
- Code summarization tasks

### Overlap Configuration

**Why Overlap Matters:**

Overlap ensures continuity between chunks. Without overlap, a chunk might end mid-thought, and the next chunk lacks context.

```python
# Example with overlap
chunk_1 = """
public void addUser(User user) {
    if (user == null) {
        return;
    }
    users.add(user);  # ← Last 200 chars included in next chunk
}
"""

chunk_2 = """
    users.add(user);  # ← Overlap from previous chunk
}

public void removeUser(String id) {
    users.removeIf(u -> u.getId().equals(id));
}
"""
```

**Recommended Overlap:**
- 15-25% of `max_chunk_size`
- Typical: 200-400 characters
- Adjust based on your use case

---

## Use Cases

### 1. Code Search and Discovery

Find code snippets by natural language description:

```python
# Find validation logic
results = db.search("email validation with regex", n_results=5)

# Find error handling
results = db.search("exception handling for database errors", n_results=5)

# Find specific patterns
results = db.search("singleton pattern implementation", n_results=3)
```

### 2. RAG (Retrieval Augmented Generation)

Use with LLMs to answer questions about your codebase:

```python
def answer_code_question(question: str, llm_client):
    # 1. Search relevant code
    results = db.search(question, n_results=5)
    
    # 2. Prepare context
    context = "\n\n".join(results['documents'][0])
    
    # 3. Query LLM with context
    prompt = f"""
    Based on this code:
    {context}
    
    Question: {question}
    """
    
    answer = llm_client.generate(prompt)
    return answer

# Usage
answer = answer_code_question(
    "How does the user validation work?",
    my_llm_client
)
```

### 3. Code Documentation Generation

Generate documentation from code chunks:

```python
# Find all methods in a class
results = db.search("UserManager class methods", n_results=20)

# Extract metadata
methods = [
    (meta['method_name'], doc)
    for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    if meta.get('method_name')
]

# Generate documentation
for method_name, code in methods:
    print(f"### {method_name}\n")
    print(f"```java\n{code}\n```\n")
```

### 4. Code Migration and Refactoring

Find similar code patterns to refactor:

```python
# Find all null checks
null_checks = db.search("null checking validation", n_results=50)

# Find deprecated API usage
deprecated = db.search("using old deprecated API methods", n_results=20)

# Find code duplication
pattern = "user authentication login logic"
similar = db.search(pattern, n_results=30)
```

### 5. Code Review Assistant

Search for potential issues:

```python
# Security concerns
security_results = db.search(
    "SQL query string concatenation injection vulnerability",
    n_results=10
)

# Performance issues
perf_results = db.search(
    "nested loops O(n^2) complexity",
    n_results=10
)

# Code smells
smell_results = db.search(
    "long method too many parameters god class",
    n_results=10
)
```

---

## Troubleshooting

### Common Issues

#### 1. "No module named 'tree_sitter_java'"

**Solution:**
```bash
pip install --upgrade tree-sitter-java
```

#### 2. ChromaDB Collection Already Exists

```python
# Delete existing collection
client = chromadb.PersistentClient(path="./chroma_db")
client.delete_collection("java_code")

# Or use get_or_create_collection (default behavior)
```

#### 3. Chunks Are Too Large/Small

**Adjust chunking parameters:**

```python
# If chunks are too large
chunker = JavaCodeChunker(
    max_chunk_size=800,  # Reduce from 1000
    min_chunk_size=100
)

# If chunks are too small
chunker = JavaCodeChunker(
    max_chunk_size=1500,  # Increase from 1000
    min_chunk_size=200    # Increase threshold
)
```

#### 4. Search Results Are Irrelevant

**Strategies:**

1. **Use more specific queries:**
   ```python
   # Instead of: "user method"
   results = db.search("method to validate user email format", n_results=5)
   ```

2. **Filter by metadata:**
   ```python
   # Search within specific class
   results = db.collection.query(
       query_texts=["validation logic"],
       where={"class_name": "UserManager"},
       n_results=5
   )
   ```

3. **Adjust n_results:**
   ```python
   # Get more results to find the right one
   results = db.search(query, n_results=20)
   ```

#### 5. Memory Issues with Large Codebases

**Process in batches:**

```python
from pathlib import Path

java_files = list(Path('src').rglob('*.java'))
batch_size = 10

for i in range(0, len(java_files), batch_size):
    batch = java_files[i:i+batch_size]
    batch_chunks = []
    
    for java_file in batch:
        with open(java_file, 'r') as f:
            code = f.read()
        chunks = chunker.chunk_code(code, str(java_file))
        batch_chunks.extend(chunks)
    
    db.add_chunks(batch_chunks)
    print(f"Processed {i+len(batch)}/{len(java_files)} files")
```

---

## Best Practices

### 1. Chunking Strategy

**DO:**
- ✅ Start with default parameters (1000/200/100)
- ✅ Adjust based on your specific use case
- ✅ Test different chunk sizes for your queries
- ✅ Use overlap to maintain context

**DON'T:**
- ❌ Make chunks too small (<300 chars) - loses context
- ❌ Make chunks too large (>3000 chars) - reduces precision
- ❌ Use zero overlap - breaks context between chunks

### 2. Metadata Usage

**Store rich metadata:**

```python
# Good: Rich metadata
metadata = {
    'file_path': 'src/auth/UserService.java',
    'class_name': 'UserService',
    'method_name': 'authenticate',
    'package': 'com.app.auth',
    'visibility': 'public',
    'is_static': 'false'
}

# Use metadata for filtering
results = db.collection.query(
    query_texts=["authentication"],
    where={
        "$and": [
            {"class_name": "UserService"},
            {"visibility": "public"}
        ]
    }
)
```

### 3. Search Query Optimization

**Effective queries:**

```python
# ✅ Good: Specific and descriptive
"method that validates email address using regex pattern"

# ❌ Bad: Too vague
"email"

# ✅ Good: Include context
"exception handling for database connection failures"

# ❌ Bad: Single word
"exception"
```

### 4. Performance Optimization

```python
# Batch processing for large datasets
db.add_chunks(chunks, batch_size=100)

# Use appropriate n_results
results = db.search(query, n_results=10)  # Don't fetch 100s

# Index management (ChromaDB handles this automatically)
# But you can create multiple collections for different projects
```

### 5. Version Control

**Store ChromaDB separately:**

```bash
# .gitignore
chroma_db/
*.chroma
```

**Document your configuration:**

```python
# config.py
CHUNKING_CONFIG = {
    'max_chunk_size': 1000,
    'chunk_overlap': 200,
    'min_chunk_size': 100
}

CHROMADB_CONFIG = {
    'collection_name': 'my_java_codebase',
    'persist_directory': './chroma_db'
}
```

### 6. Testing

**Always test with sample searches:**

```python
def validate_chunking(db_manager):
    """Test search quality."""
    test_queries = [
        ("user validation", "addUser"),
        ("remove user logic", "removeUser"),
        ("get all users", "getAllUsers")
    ]
    
    for query, expected_method in test_queries:
        results = db_manager.search(query, n_results=1)
        actual_method = results['metadatas'][0][0].get('method_name', '')
        
        if actual_method == expected_method:
            print(f"✓ '{query}' → {actual_method}")
        else:
            print(f"✗ '{query}' → {actual_method} (expected {expected_method})")

validate_chunking(db)
```

---

## Complete Example: Production Workflow

```python
import os
from pathlib import Path
from java_code_chunker import JavaCodeChunker, ChromaDBManager

def production_workflow(
    project_path: str,
    collection_name: str,
    config: dict = None
):
    """
    Production-ready workflow for processing Java codebase.
    """
    # Configuration
    config = config or {
        'max_chunk_size': 1000,
        'chunk_overlap': 200,
        'min_chunk_size': 100,
        'batch_size': 50,
        'persist_dir': './production_db'
    }
    
    # Initialize
    chunker = JavaCodeChunker(
        max_chunk_size=config['max_chunk_size'],
        chunk_overlap=config['chunk_overlap'],
        min_chunk_size=config['min_chunk_size']
    )
    
    db = ChromaDBManager(
        collection_name=collection_name,
        persist_directory=config['persist_dir']
    )
    
    # Process files
    java_files = list(Path(project_path).rglob('*.java'))
    print(f"Found {len(java_files)} Java files")
    
    all_chunks = []
    for i, java_file in enumerate(java_files, 1):
        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            chunks = chunker.chunk_code(code, str(java_file))
            all_chunks.extend(chunks)
            
            # Batch processing
            if len(all_chunks) >= config['batch_size']:
                db.add_chunks(all_chunks[:config['batch_size']])
                all_chunks = all_chunks[config['batch_size']:]
            
            if i % 10 == 0:
                print(f"Processed {i}/{len(java_files)} files")
                
        except Exception as e:
            print(f"Error processing {java_file}: {e}")
            continue
    
    # Add remaining chunks
    if all_chunks:
        db.add_chunks(all_chunks)
    
    print(f"✓ Complete! Total chunks: {db.collection.count()}")
    return db

# Usage
db = production_workflow(
    project_path='src/main/java',
    collection_name='my_production_codebase'
)

# Search
results = db.search("authentication and authorization logic", n_results=10)
```

---

## Conclusion

This system provides a robust, production-ready solution for chunking and searching Java code. The combination of tree-based parsing and semantic search enables powerful code discovery and retrieval capabilities.

For questions or issues, refer to the Jupyter notebook for interactive examples and testing.
