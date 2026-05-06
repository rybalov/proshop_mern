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