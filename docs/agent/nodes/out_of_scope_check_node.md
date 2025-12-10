out_of_scope_check_node summary

Location: `llm/StategraphAgent.py` (`out_of_scope_check_node` function)

### Control flow
1. Look up the detector that classifies a query as "valid" or "out_of_scope" and, when valid, emits 2-5 expressive keyword phrases tailored for literature search.
2. If that detector is unavailable, set `state["error"] = "detect_out_of_scope_query tool not found"` and return immediately.
3. Pass the raw `user_query` to the detector so it can run its LLM prompt (which checks for nonsensical topics, greetings, etc., and extracts keywords following the specificity rules from `detect_out_of_scope_query`).
4. Save the detector's response (status, reason, keywords) on the state for downstream QC and filtering steps, then return the updated state.

### State mutations
- `out_of_scope_result`: always overwritten with the tool response (string or JSON).
- `error`: only set when the tool cannot be located; left untouched otherwise.
