---
name: lightrag-query
description: >
  Query the LightRAG knowledge base with flexible streaming responses. Use when the user
  wants to ask questions, search the knowledge graph, retrieve documents, or perform RAG
  queries. Supports multiple query modes (local, global, hybrid, naive, mix, bypass) with
  real-time streaming or complete response delivery.
allowed-tools: Bash Read Write Edit Glob Grep
---

# LightRAG Query

Query the LightRAG knowledge base through the `/query/stream` endpoint with flexible retrieval and streaming options.

## Endpoint

```
POST http://0.0.0.0:9621/query/stream
```

## Query Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `local` | Entity-focused retrieval with direct relationships | Specific entity lookups |
| `global` | Pattern analysis across the knowledge graph | Exploring concepts broadly |
| `hybrid` | Combined local and global strategies | Balanced retrieval |
| `naive` | Vector similarity search only | Fast semantic search |
| `mix` | Integrated knowledge graph + vector retrieval | **Recommended for most use cases** |
| `bypass` | Direct LLM query without knowledge retrieval | Fallback when no docs match |

## Request Format

```json
{
    "query": "Your question here",
    "mode": "mix",
    "stream": true,
    "include_references": true,
    "response_type": "Multiple Paragraphs",
    "top_k": 10,
    "conversation_history": [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ],
    "max_total_tokens": 4096,
    "hl_keywords": ["high", "level", "keywords"],
    "ll_keywords": ["low", "level", "keywords"]
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | The question/prompt (min 3 characters) |
| `mode` | string | `"mix"` | Query strategy |
| `stream` | boolean | `true` | Enable streaming response |
| `include_references` | boolean | `false` | Include source citations |
| `response_type` | string | varies | Format preference (e.g., "Multiple Paragraphs", "Single Paragraph", "Bullet Points") |
| `top_k` | integer | - | Number of top entities/relations to retrieve |
| `conversation_history` | array | `[]` | Previous dialogue for multi-turn conversations |
| `max_total_tokens` | integer | - | Token budget for entire response |
| `hl_keywords` | array | - | High-level keywords (bypasses LLM keyword extraction) |
| `ll_keywords` | array | - | Low-level keywords (bypasses LLM keyword extraction) |

## Response Format

### Streaming Mode (stream: true)

Returns NDJSON — each line is a separate JSON object:

**First line** (if `include_references: true`):
```json
{"references": [{"source": "...", "content": "...", "score": 0.95}, ...]}
```

**Content chunks:**
```json
{"response": "content chunk"}
```

**Errors:**
```json
{"error": "error message"}
```

### Non-Streaming Mode (stream: false)

Complete response in a single message:
```json
{"references": [...], "response": "complete content"}
```

## Processing Examples

### Python (streaming)

```python
import httpx
import json

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://0.0.0.0:9621/query/stream",
        json={"query": "Explain machine learning", "mode": "mix", "stream": True}
    )
    async for line in response.iter_lines():
        data = json.loads(line)
        if "references" in data:
            print(f"References: {data['references']}")
        if "response" in data:
            print(f"Chunk: {data['response']}", end="")
        if "error" in data:
            print(f"Error: {data['error']}")
```

### Python (non-streaming)

```python
import httpx

response = httpx.post(
    "http://0.0.0.0:9621/query/stream",
    json={"query": "What is deep learning?", "mode": "mix", "stream": False}
).json()

print(response["response"])
if response.get("references"):
    print(f"\nSources: {response['references']}")
```

### JavaScript (Node.js)

```javascript
const response = await fetch('http://0.0.0.0:9621/query/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: "Explain neural networks",
        mode: "mix",
        stream: true,
        include_references: true
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const line = decoder.decode(value);
    const data = JSON.parse(line);
    
    if (data.references) console.log('Sources:', data.references);
    if (data.response) process.stdout.write(data.response);
    if (data.error) console.error('Error:', data.error);
}
```

## Error Handling

| Status | Cause | Example |
|--------|-------|---------|
| 400 | Invalid input (query too short, invalid mode) | `{"detail": "Query must be at least 3 characters"}` |
| 500 | Internal error (LLM unavailable, graph error) | `{"error": "LLM service unavailable"}` |

## Bypass Mode for Keyword Extraction

When you already have keywords, bypass the LLM extraction:

```json
{
    "query": "What is RAG?",
    "hl_keywords": ["machine learning", "information retrieval"],
    "ll_keywords": ["retrieval augmented generation", "knowledge base"],
    "mode": "mix"
}
```

## Conversation History

Pass multi-turn context (sent to LLM only, doesn't affect retrieval):

```json
{
    "query": "Can you elaborate on that?",
    "stream": true,
    "conversation_history": [
        {"role": "user", "content": "What is a neural network?"},
        {"role": "assistant", "content": "A neural network is..."}
    ]
}
```

## Tips

- Use **`mix` mode** for best overall results
- Set **`include_references: true`** when you need source citations
- **Stream for real-time UI** — non-streaming waits for complete response
- Use **`hl_keywords`/`ll_keywords`** to bypass extraction when you have domain knowledge
- Check for **`error`** objects in every chunk when streaming

## Related Skills

- `/lightrag-insert` — add documents to the knowledge base
- `/lightrag-status` — check system health and stats