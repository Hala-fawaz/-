# Task 2 architecture

```text
User
  |
  v
Next.js UI
  |---- Language selector (32+)
  |---- Question input
  |---- Interactive Atlas
  |
  v
FastAPI
  |
  +--> AI Router
  |      |
  |      +--> RAG / LlamaIndex
  |      |       |
  |      |       +--> ChromaDB
  |      |
  |      +--> Translation Adapter
  |
  v
Grounded answer + references
```

## Later integration

- Replace the current visual map with Three.js + Cesium.
- Connect question submission to the FastAPI RAG endpoint.
- Add LlamaIndex retrieval.
- Add ChromaDB vector search.
- Add the approved historical/religious corpus.
- Add the project's safety/abstention router.
- Add a production-approved multilingual model/provider.
