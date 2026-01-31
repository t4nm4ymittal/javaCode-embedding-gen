# Java Code Chunking Process - Visual Explanation

## Example Java Code

Let's use this sample Java class to demonstrate the chunking process:

```java
package com.example.app;

import java.util.List;
import java.util.ArrayList;

/**
 * UserManager handles user operations
 */
public class UserManager {
    
    private List<User> users;
    private int maxUsers = 100;
    
    public UserManager() {
        this.users = new ArrayList<>();
    }
    
    public boolean addUser(User user) {
        if (user == null) {
            return false;
        }
        users.add(user);
        return true;
    }
    
    public User getUser(String id) {
        return users.stream()
            .filter(u -> u.getId().equals(id))
            .findFirst()
            .orElse(null);
    }
}
```

---

## Step-by-Step Process Visualization

### STEP 1: Parse Code into AST (Abstract Syntax Tree)

```
Input: Java Code (String)
   ↓
tree_sitter Parser
   ↓
AST Tree Structure
```

**What happens:**
- Tree-sitter reads the Java code
- Converts it into a hierarchical tree structure
- Each node represents a code element (class, method, field, etc.)

**AST Visualization:**

```
program (root)
├── package_declaration
│   └── "package com.example.app;"
│
├── import_declaration  
│   └── "import java.util.List;"
│
├── import_declaration
│   └── "import java.util.ArrayList;"
│
└── class_declaration (UserManager)
    ├── modifiers: ["public"]
    ├── name: "UserManager"
    └── class_body
        ├── field_declaration (users)
        │   ├── type: List<User>
        │   └── name: "users"
        │
        ├── field_declaration (maxUsers)
        │   ├── type: int
        │   └── name: "maxUsers"
        │
        ├── constructor_declaration
        │   ├── name: "UserManager"
        │   └── body: { this.users = new ArrayList<>(); }
        │
        ├── method_declaration (addUser)
        │   ├── return_type: boolean
        │   ├── name: "addUser"
        │   ├── parameters: (User user)
        │   └── body: { if (user == null) ... }
        │
        └── method_declaration (getUser)
            ├── return_type: User
            ├── name: "getUser"
            ├── parameters: (String id)
            └── body: { return users.stream() ... }
```

---

### STEP 2: Process Top-Level Nodes

```
Root Node Children:
┌─────────────────────┐
│ package_declaration │ → Process → Create Chunk #1
├─────────────────────┤
│ import_declaration  │ → Process → Create Chunk #2
├─────────────────────┤
│ import_declaration  │ → Process → Create Chunk #3
├─────────────────────┤
│ class_declaration   │ → Process → (Split further)
└─────────────────────┘
```

**Code Flow:**

```python
for child in root_node.children:
    chunks.extend(self._process_node(child, source_bytes, file_path))
```

**What _process_node() does:**

```
Input: AST Node
   ↓
Check node.type
   ↓
├─ package_declaration? → Create 1 chunk
├─ import_declaration?  → Create 1 chunk  
├─ class_declaration?   → Call _process_class()
├─ interface_declaration? → Call _process_class()
└─ comment?             → Create 1 chunk
```

---

### STEP 3: Process Class Declaration

When we encounter the `class_declaration` node, we dive deeper:

```
class_declaration (UserManager)
   ↓
Find class_body
   ↓
For each child in class_body:
   ├─ field_declaration → Create Chunk
   ├─ method_declaration → Create Chunk
   └─ constructor_declaration → Create Chunk
```

**Detailed Process:**

```
UserManager Class Body
┌──────────────────────────────────┐
│ field: private List<User> users; │ → Chunk #4 (field)
├──────────────────────────────────┤
│ field: private int maxUsers=100; │ → Chunk #5 (field)
├──────────────────────────────────┤
│ constructor: UserManager() {...} │ → Chunk #6 (method)
├──────────────────────────────────┤
│ method: addUser(User user) {...} │ → Chunk #7 (method)
├──────────────────────────────────┤
│ method: getUser(String id) {...} │ → Chunk #8 (method)
└──────────────────────────────────┘
```

---

### STEP 4: Create Chunks with Metadata

For each AST node, create a `CodeChunk` object:

```
┌─────────────────────────────────────────────────────┐
│ Chunk #1                                            │
├─────────────────────────────────────────────────────┤
│ content: "package com.example.app;"                 │
│ start_line: 1                                       │
│ end_line: 1                                         │
│ chunk_type: "package"                               │
│ metadata: {                                         │
│   'file_path': 'UserManager.java',                 │
│   'node_type': 'package_declaration',              │
│   'length': 24                                      │
│ }                                                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Chunk #2                                            │
├─────────────────────────────────────────────────────┤
│ content: "import java.util.List;"                   │
│ start_line: 3                                       │
│ end_line: 3                                         │
│ chunk_type: "import"                                │
│ metadata: {                                         │
│   'file_path': 'UserManager.java',                 │
│   'node_type': 'import_declaration',               │
│   'length': 24                                      │
│ }                                                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Chunk #7                                            │
├─────────────────────────────────────────────────────┤
│ content: "public boolean addUser(User user) {       │
│     if (user == null) {                             │
│         return false;                               │
│     }                                               │
│     users.add(user);                                │
│     return true;                                    │
│ }"                                                  │
│ start_line: 17                                      │
│ end_line: 23                                        │
│ chunk_type: "method"                                │
│ metadata: {                                         │
│   'file_path': 'UserManager.java',                 │
│   'class_name': 'UserManager',                     │
│   'method_name': 'addUser',                        │
│   'node_type': 'method_declaration',               │
│   'length': 145                                     │
│ }                                                   │
└─────────────────────────────────────────────────────┘
```

---

### STEP 5: Merge Small Chunks

```
Before Merging (min_chunk_size = 100):
┌──────────────────┐
│ Chunk #1: 24 chr │ ← Too small
├──────────────────┤
│ Chunk #2: 24 chr │ ← Too small
├──────────────────┤
│ Chunk #3: 30 chr │ ← Too small
├──────────────────┤
│ Chunk #4: 145 chr│ ✓ Big enough
├──────────────────┤
│ Chunk #5: 180 chr│ ✓ Big enough
└──────────────────┘

After Merging:
┌──────────────────────────────────┐
│ Merged Chunk: 78 chr             │ ← Chunks #1 + #2 + #3
│ (package + imports)              │
├──────────────────────────────────┤
│ Chunk #4: 145 chr                │ ← Unchanged
├──────────────────────────────────┤
│ Chunk #5: 180 chr                │ ← Unchanged
└──────────────────────────────────┘
```

**Code Logic:**

```python
if len(chunk.content) < self.min_chunk_size:
    # Merge with previous small chunk
    current_merged = CodeChunk(
        content=current_merged.content + "\n" + chunk.content,
        ...
    )
else:
    # Chunk is big enough, keep it separate
    merged.append(chunk)
```

---

### STEP 6: Add Overlap Between Chunks

```
chunk_overlap = 200 characters

Before Overlap:
┌────────────────────────────────────┐
│ Chunk A (600 chars)                │
│ "public UserManager() {            │
│     this.users = new ArrayList<>();│
│ }"                                 │
└────────────────────────────────────┘
┌────────────────────────────────────┐
│ Chunk B (400 chars)                │
│ "public boolean addUser(...) {     │
│     ...                            │
│ }"                                 │
└────────────────────────────────────┘

After Adding Overlap:
┌────────────────────────────────────┐
│ Chunk A (600 chars)                │
│ "public UserManager() {            │
│     this.users = new ArrayList<>();│
│ }"                                 │
└────────────────────────────────────┘
┌────────────────────────────────────┐
│ Chunk B (600 chars)                │
│ ┌──────────────────────────────┐   │
│ │ OVERLAP (last 200 from A)    │   │
│ │ "    this.users = new Arr... │   │
│ └──────────────────────────────┘   │
│ "public boolean addUser(...) {     │
│     ...                            │
│ }"                                 │
└────────────────────────────────────┘
```

**Why Overlap?**

Without overlap, Chunk B starts abruptly. With overlap, it has context from Chunk A.

**Visual Example:**

```
WITHOUT OVERLAP:
Chunk B starts here ↓
public boolean addUser(User user) {
    if (user == null) {
        return false;
    }
    ...
}

WITH OVERLAP (200 chars from previous chunk):
    this.users = new ArrayList<>();  ← Context from Chunk A
}                                     ← End of previous method

public boolean addUser(User user) {  ← Chunk B starts here
    if (user == null) {
        return false;
    }
    ...
}
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: Java Source Code                  │
│                  (UserManager.java - 35 lines)              │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: Parse with tree-sitter                 │
│                                                             │
│  Code (String) → tree.parse() → AST (Tree Structure)       │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│        STEP 2: Traverse AST & Identify Top-Level Nodes      │
│                                                             │
│  root_node.children → [package, import, import, class]     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│           STEP 3: Process Each Node Type                    │
│                                                             │
│  ├─ package_declaration → Create chunk                     │
│  ├─ import_declaration  → Create chunk                     │
│  └─ class_declaration   → DIVE DEEPER ↓                    │
│                                                             │
│      class_body.children → [field, field, method, ...]     │
│      ├─ field_declaration → Create chunk                   │
│      ├─ method_declaration → Create chunk                  │
│      └─ constructor_declaration → Create chunk             │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         STEP 4: Create CodeChunk Objects                    │
│                                                             │
│  For each AST node:                                         │
│  CodeChunk(                                                 │
│    content = node.text,                                     │
│    start_line = node.start_line,                           │
│    end_line = node.end_line,                               │
│    chunk_type = "method" | "class" | "import",             │
│    metadata = {file_path, class_name, method_name, ...}    │
│  )                                                          │
│                                                             │
│  Result: [Chunk1, Chunk2, ..., Chunk8]                     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│    STEP 5: Merge Small Chunks (< min_chunk_size)           │
│                                                             │
│  Before: [24chr, 24chr, 30chr, 145chr, 180chr]             │
│           ↓      ↓      ↓                                  │
│  After:  [78chr (merged), 145chr, 180chr]                  │
│                                                             │
│  Result: [Chunk1, Chunk2, Chunk3]                          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Add Overlap Between Chunks (chunk_overlap chars)  │
│                                                             │
│  Chunk1: [original content]                                │
│  Chunk2: [last 200 chars of Chunk1] + [original content]  │
│  Chunk3: [last 200 chars of Chunk2] + [original content]  │
│                                                             │
│  Result: [Chunk1, Chunk2_overlap, Chunk3_overlap]          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 OUTPUT: List[CodeChunk]                     │
│                                                             │
│  Each chunk ready for ChromaDB storage with:               │
│  • Meaningful code content                                 │
│  • Rich metadata (file, class, method names)               │
│  • Preserved code structure                                │
│  • Context through overlap                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Real Example with Actual Numbers

Let's trace through our UserManager.java example:

### Input Stats:
- **Total lines:** 35
- **Total characters:** ~850
- **Classes:** 1 (UserManager)
- **Methods:** 3 (constructor, addUser, getUser)
- **Fields:** 2 (users, maxUsers)
- **Imports:** 2

### Configuration:
```python
max_chunk_size = 1000
chunk_overlap = 200
min_chunk_size = 100
```

### Output After Processing:

```
┌──────────────────────────────────────────────────────────┐
│ CHUNK 1 (Merged: package + imports)                     │
├──────────────────────────────────────────────────────────┤
│ Type: merged                                             │
│ Lines: 1-4                                               │
│ Size: 78 characters                                      │
│ Content:                                                 │
│   package com.example.app;                              │
│   import java.util.List;                                │
│   import java.util.ArrayList;                           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ CHUNK 2 (Field declarations)                            │
├──────────────────────────────────────────────────────────┤
│ Type: field                                              │
│ Lines: 10-11                                             │
│ Size: 120 characters                                     │
│ Metadata: class_name="UserManager"                      │
│ Content:                                                 │
│   private List<User> users;                             │
│   private int maxUsers = 100;                           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ CHUNK 3 (Constructor) + OVERLAP                         │
├──────────────────────────────────────────────────────────┤
│ Type: method                                             │
│ Lines: 13-15                                             │
│ Size: 145 characters (+ 200 overlap)                     │
│ Metadata: class_name="UserManager",                     │
│           method_name="UserManager"                      │
│ Has overlap: True                                        │
│ Content:                                                 │
│   [200 chars overlap from previous chunk]               │
│   public UserManager() {                                │
│       this.users = new ArrayList<>();                   │
│   }                                                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ CHUNK 4 (addUser method) + OVERLAP                      │
├──────────────────────────────────────────────────────────┤
│ Type: method                                             │
│ Lines: 17-23                                             │
│ Size: 180 characters (+ 200 overlap)                     │
│ Metadata: class_name="UserManager",                     │
│           method_name="addUser"                          │
│ Has overlap: True                                        │
│ Content:                                                 │
│   [200 chars overlap from previous chunk]               │
│   public boolean addUser(User user) {                   │
│       if (user == null) {                               │
│           return false;                                 │
│       }                                                  │
│       users.add(user);                                  │
│       return true;                                      │
│   }                                                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ CHUNK 5 (getUser method) + OVERLAP                      │
├──────────────────────────────────────────────────────────┤
│ Type: method                                             │
│ Lines: 25-30                                             │
│ Size: 210 characters (+ 200 overlap)                     │
│ Metadata: class_name="UserManager",                     │
│           method_name="getUser"                          │
│ Has overlap: True                                        │
│ Content:                                                 │
│   [200 chars overlap from previous chunk]               │
│   public User getUser(String id) {                      │
│       return users.stream()                             │
│           .filter(u -> u.getId().equals(id))            │
│           .findFirst()                                  │
│           .orElse(null);                                │
│   }                                                      │
└──────────────────────────────────────────────────────────┘
```

### Summary Statistics:
- **Input:** 1 file, 850 characters
- **Output:** 5 chunks
- **Average chunk size:** 147 characters (without overlap)
- **With overlap:** ~347 characters per chunk
- **Metadata richness:** File path, class name, method names all preserved

---

## Key Benefits Illustrated

### 🎯 Semantic Boundaries Preserved

**Bad (Simple text splitting):**
```
Chunk 1: "...users.add(user);\n    return tr"
Chunk 2: "ue;\n}\n\npublic User getUser(Str..."
         ↑ Method split in the middle!
```

**Good (Tree-based):**
```
Chunk 1: Complete addUser() method
Chunk 2: Complete getUser() method
         ↑ Each chunk is meaningful!
```

### 📊 Rich Metadata for Search

```
Query: "method to validate and add user"
        ↓
ChromaDB searches embeddings
        ↓
Finds: Chunk 4 (addUser method)
       metadata.method_name = "addUser"
       metadata.class_name = "UserManager"
        ↓
Returns complete, contextualized code!
```

### 🔗 Context Through Overlap

```
User searches: "how to add user"
Retrieves: Chunk 4 (addUser)
Gets:
  - Overlap: Constructor showing field initialization
  - Main: addUser method with validation
  - Context: Understanding of the class structure
```

This is why tree-based chunking is superior to simple text splitting!
