---
name: lightrag-api
description: "Interact with LightRAG API for document management, RAG queries, and knowledge graph operations. Use when uploading documents, querying the knowledge base, or managing entities/relations in LightRAG. Base URL: http://localhost:9621"
---

# LightRAG API Skill

This skill enables interaction with the LightRAG server API for document management, RAG queries, and knowledge graph operations.

**Base URL:** `http://localhost:9621`

**Authentication:** OAuth2 Password Bearer (optional API key via `api_key_header_value` query param)

---

## Document Management

### Upload Document
```bash
curl -X POST "http://localhost:9621/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

### Insert Text
```bash
curl -X POST "http://localhost:9621/documents/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Content to index", "file_name": "note.txt", "track_id": "optional-id"}'
```

### Insert Multiple Texts
```bash
curl -X POST "http://localhost:9621/documents/texts" \
  -H "Content-Type: application/json" \
  -d '{"texts": [{"text": "First text"}, {"text": "Second text"}], "track_id": "optional-id"}'
```

### Scan for New Documents
```bash
curl -X POST "http://localhost:9621/documents/scan"
```

### Get Pipeline Status
```bash
curl -X GET "http://localhost:9621/documents/pipeline_status"
```

### Get Document Status Counts
```bash
curl -X GET "http://localhost:9621/documents/status_counts"
```

### Get Documents Paginated
```bash
curl -X POST "http://localhost:9621/documents/paginated" \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "page_size": 20, "status": "PROCESSED"}'
```

### Track Document Status
```bash
curl -X GET "http://localhost:9621/documents/track_status/{track_id}"
```

### Reprocess Failed Documents
```bash
curl -X POST "http://localhost:9621/documents/reprocess_failed"
```

### Cancel Pipeline
```bash
curl -X POST "http://localhost:9621/documents/cancel_pipeline"
```

### Clear All Documents
```bash
curl -X DELETE "http://localhost:9621/documents"
```

### Delete Specific Document
```bash
curl -X DELETE "http://localhost:9621/documents/delete_document" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": ["doc-id-1", "doc-id-2"]}'
```

### Clear LLM Cache
```bash
curl -X POST "http://localhost:9621/documents/clear_cache" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## RAG Queries

### Query (Non-Streaming)
```bash
curl -X POST "http://localhost:9621/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "mode": "mix",
    "include_references": true
  }'
```

### Query (Streaming)
```bash
curl -X POST "http://localhost:9621/query/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain neural networks",
    "mode": "hybrid",
    "stream": true
  }'
```

### Query Modes:
| Mode | Description |
|------|-------------|
| `local` | Focus on specific entities and direct relationships |
| `global` | Analyze broader patterns across the knowledge graph |
| `hybrid` | Combines local and global approaches |
| `naive` | Simple vector similarity search |
| `mix` | Integrates knowledge graph with vector search (recommended) |
| `bypass` | Direct LLM query without knowledge retrieval |

### Query Request Body:
```json
{
  "query": "Your question here",
  "mode": "mix",
  "top_k": 10,
  "include_references": true,
  "include_chunk_content": false,
  "response_type": "Multiple Paragraphs",
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ],
  "hl_keywords": ["high", "level", "keywords"],
  "ll_keywords": ["low", "level", "keywords"],
  "max_total_tokens": 16000
}
```

---

## Knowledge Graph Operations

### List All Entities
```bash
curl -X GET "http://localhost:9621/graphs"
```

### List Entity Labels
```bash
curl -X GET "http://localhost:9621/graph/label/list"
```

### Search Popular Labels
```bash
curl -X GET "http://localhost:9621/graph/label/popular?limit=20"
```

### Search Labels
```bash
curl -X GET "http://localhost:9621/graph/label/search?query=AI"
```

### Check Entity Exists
```bash
curl -X GET "http://localhost:9621/graph/entity/exists?entity_name=Python"
```

### Create Entity
```bash
curl -X POST "http://localhost:9621/graph/entity/create" \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "Python", "entity_type": "Programming Language"}'
```

### Edit Entity
```bash
curl -X POST "http://localhost:9621/graph/entity/edit" \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "Python", "new_name": "Python Lang", "new_type": "Language"}'
```

### Delete Entity
```bash
curl -X DELETE "http://localhost:9621/documents/delete_entity" \
  -H "Content-Type: application/json" \
  -d '{"entity_name": "Python"}'
```

### Create Relation
```bash
curl -X POST "http://localhost:9621/graph/relation/create" \
  -H "Content-Type: application/json" \
  -d '{"src_id": "entity1", "tgt_id": "entity2", "relation_type": "related_to"}'
```

### Edit Relation
```bash
curl -X POST "http://localhost:9621/graph/relation/edit" \
  -H "Content-Type: application/json" \
  -d '{"src_id": "entity1", "tgt_id": "entity2", "new_relation_type": "uses"}'
```

### Delete Relation
```bash
curl -X DELETE "http://localhost:9621/documents/delete_relation" \
  -H "Content-Type: application/json" \
  -d '{"src_id": "entity1", "tgt_id": "entity2", "relation_type": "related_to"}'
```

### Merge Entities
```bash
curl -X POST "http://localhost:9621/graph/entities/merge" \
  -H "Content-Type: application/json" \
  -d '{"src_ids": ["entity1", "entity2"], "tgt_id": "merged_entity"}'
```

---

## System & Utilities

### Health Check
```bash
curl -X GET "http://localhost:9621/health"
```

### Get API Version
```bash
curl -X GET "http://localhost:9621/api/version"
```

### List API Tags
```bash
curl -X GET "http://localhost:9621/api/tags"
```

### Get Process Status
```bash
curl -X GET "http://localhost:9621/api/ps"
```

### Check Auth Status
```bash
curl -X GET "http://localhost:9621/auth-status"
```

### Login
```bash
curl -X POST "http://localhost:9621/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:9621"

def upload_document(file_path: str) -> dict:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/documents/upload", files=files)
    return response.json()

def query(query_text: str, mode: str = "mix", include_references: bool = True) -> dict:
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": query_text,
            "mode": mode,
            "include_references": include_references
        }
    )
    return response.json()

def insert_text(text: str, file_name: str = "note.txt") -> dict:
    response = requests.post(
        f"{BASE_URL}/documents/text",
        json={"text": text, "file_name": file_name}
    )
    return response.json()

def get_pipeline_status() -> dict:
    response = requests.get(f"{BASE_URL}/documents/pipeline_status")
    return response.json()

def get_documents(page: int = 1, page_size: int = 20) -> dict:
    response = requests.post(
        f"{BASE_URL}/documents/paginated",
        json={"page": page, "page_size": page_size}
    )
    return response.json()
```

---

## Common Workflows

### 1. Upload and Query
```bash
# Upload a document
curl -X POST "http://localhost:9621/documents/upload" -F "file=@report.pdf"

# Wait for processing, then query
curl -X POST "http://localhost:9621/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the key findings", "mode": "mix"}'
```

### 2. Batch Insert and Query
```bash
# Insert multiple texts
curl -X POST "http://localhost:9621/documents/texts" \
  -H "Content-Type: application/json" \
  -d '{"texts": [{"text": "AI is transforming industries"}, {"text": "Machine learning enables predictions"}]}'

# Query with conversation history
curl -X POST "http://localhost:9621/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me more about ML", "mode": "mix", "conversation_history": [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI is artificial intelligence..."}]}'
```

### 3. Knowledge Graph Exploration
```bash
# Get all entities
curl -X GET "http://localhost:9621/graphs"

# Search for AI-related labels
curl -X GET "http://localhost:9621/graph/label/search?query=AI"

# Check if entity exists
curl -X GET "http://localhost:9621/graph/entity/exists?entity_name=Machine%20Learning"
```
