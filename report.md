# M2 — Report

## IDE

GitHub Copilot CLI 

## Rules diff

1. Add section "5.0 Code Style" - to ensure a consistent and readable codebase.
2. Add section "5.4 Error Handling" - to ensure consistent and robust error management across the codebase.
3. Add section "7. Pull Request Approval Criteria" - to maintain the quality of the project.

# M3 — Report

## Feature flags MCP

**Step 1 — get_feature_info**

Tool: `get_feature_info`
Arguments: `{ "feature_name": "search_v2" }`
Response:
```json
{
  "key": "search_v2",
  "name": "New Search Algorithm",
  "description": "Replaces legacy regex-based keyword matching with a hybrid BM25 + TF-IDF ranking pipeline...",
  "status": "Testing",
  "traffic_percentage": 15,
  "last_modified": "2026-03-10",
  "targeted_segments": ["beta_users", "internal"],
  "rollout_strategy": "canary",
  "depends_on": []
}
```
Observation: Feature was already in **Testing** (not Disabled), so no state change was needed.

**Step 2 — adjust_traffic_rollout**

Tool: `adjust_traffic_rollout`
Arguments: `{ "feature_name": "search_v2", "percentage": 25 }`
Response:
```json
{
  "key": "search_v2",
  "name": "New Search Algorithm",
  "status": "Testing",
  "traffic_percentage": 25,
  "last_modified": "2026-05-06",
  "depends_on": []
}
```
Traffic successfully updated from 15% to 25%.

**Step 3 — get_feature_info (confirmation)**

Tool: `get_feature_info`
Arguments: `{ "feature_name": "search_v2" }`
Response:
```json
{
  "key": "search_v2",
  "name": "New Search Algorithm",
  "status": "Testing",
  "traffic_percentage": 25,
  "last_modified": "2026-05-06",
  "targeted_segments": ["beta_users", "internal"],
  "rollout_strategy": "canary",
  "depends_on": []
}
```

**Final state:**

| Field         | Value       |
|---------------|-------------|
| Key           | `search_v2` |
| Status        | Testing     |
| Traffic       | 25%         |
| Last modified | 2026-05-06  |
| Dependencies  | None        |

---

## RAG Documentation Corpus

### Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Embedding model | OpenAI `text-embedding-3-small` | Managed API, multilingual, 1536 dims, $0.02/1M tokens — cheapest production-quality option |
| Vector DB | pgvector (PostgreSQL 17) | Already in docker-compose; native SQL interface; IVFFlat index for cosine similarity |
| Chunking | Custom Python script | Semantic splitting by markdown headings; preserves document structure |
| Client library | `openai` Python SDK + `psycopg2` | Standard, well-maintained, minimal dependencies |

### Repository artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Chunking script | `scripts/chunk_markdown.py` | Splits 47 markdown files into semantic chunks |
| Ingestion script | `scripts/embed_chunks.py` | Embeds chunks with OpenAI and loads into pgvector |
| Search script | `scripts/search_chunks.py` | CLI semantic search with optional pre-filters |
| Python deps | `scripts/requirements.txt` | `openai`, `psycopg2-binary`, `python-dotenv` |
| Chunks corpus | `docs/project-data/chunks.jsonl` | 723 chunks with text + metadata (full corpus, not a sample) |

### Chunking parameters

- **Target size:** 400 tokens, max 600, min 50
- **Strategy:** Semantic — split by H1/H2/H3 headings; tables split by rows preserving header
- **Overlap:** Only when cutting mid-paragraph (1 sentence)
- **Metadata per chunk:** `source_file`, `file_path`, `title`, `parent_headings`, `keywords`, `summary`, `language`

### Test queries

**Query 1:** "Какая БД используется в proshop_mern и почему именно она?"
(Factual single-hop — expected: ADR about MongoDB choice)

| # | Score | Source | Section |
|---|-------|--------|---------|
| 1 | 0.319 | features/cart.md | Cart Persistence > Зависимости |
| 2 | 0.314 | features/admin.md | Admin Product Delete > API endpoints |
| 3 | 0.313 | architecture.md | Data Layer > Collection: orders |

**Verdict:** ❌ Missed the target chunk (`adrs/adr-001-mongodb`). Low scores overall (0.31–0.32). The ADR chunk likely lacks explicit phrasing "какая БД и почему" — the title/headings context is not embedded with the text.

---

**Query 2:** "Какие фичи зависят от payment_stripe_v3?"
(Multi-hop dependency query)

| # | Score | Source | Section |
|---|-------|--------|---------|
| 1 | 0.478 | features/checkout.md | Payment Method Selection > User flow |
| 2 | 0.457 | features-analysis-ru.md | M4 Figma-прототипирование > Слабые кандидаты |
| 3 | 0.453 | pages/payment.md | Route |

**Verdict:** ⚠️ Topically relevant (payments/stripe domain), but doesn't answer the exact dependency graph question. Feature flag dependency data lives in `backend/features.json` (not chunked — it's JSON, not markdown).

---

**Query 3:** "Что случилось во время последнего incident с checkout?"
(Filtered retrieval — `--type incidents`)

| # | Score | Source | Section |
|---|-------|--------|---------|
| 1 | 0.424 | incidents/i-002-mongo-connection-pool-exhaustion.md | Impact |
| 2 | 0.409 | incidents/i-001-paypal-double-charge.md | Impact |
| 3 | 0.398 | incidents/i-001-paypal-double-charge.md | Timeline |

**Verdict:** ✅ With the `--type incidents` pre-filter, results are highly relevant. Both incident reports surface with their Impact sections first — ideal for answering "what happened" questions.

### Reflection

We chose OpenAI `text-embedding-3-small` over local models (BGE-M3, nomic) primarily for simplicity and reliability — no GPU required, no Ollama container to manage, and the cost for 723 chunks is negligible ($0.001). pgvector was the natural vector store since the PostgreSQL container was already part of our docker-compose stack, eliminating the need for a dedicated vector DB like Qdrant or Pinecone. The chunking pipeline (semantic splitting by markdown headings) works well for structured documentation but struggles with the ADR query because chunk text alone doesn't always carry enough context about *what question the document answers* — enriching embeddings with title + parent_headings prepended to the text would likely fix this. The pre-filter mechanism (`--source_file`, `--type`) proved critical for targeted queries and should be the default approach when an agent knows the document category. The main limitation is that our corpus is markdown-only: structured data like `features.json` isn't indexed, so dependency-graph questions require the MCP tools rather than RAG. If we were to redo this, we would (1) prepend metadata context to chunk text before embedding, (2) include JSON/YAML sources as chunked prose, and (3) add a hybrid keyword search (BM25) alongside vector similarity for exact-match queries.