# IDE Changes: 008 - Increase Extraction Token Limit & Handle Length Limits

## Summary
- Resolved OpenAI `LengthFinishReasonError` encountered during candidate profile extraction for candidates with extensive resumes and GitHub repositories:
  - In `.env`, `.env.example`, and `backend/app/config.py`, increased `MAX_OUTPUT_TOKENS_EXTRACTION` from `2500` to `4000` tokens, ensuring rich candidate profiles with multiple projects, repos, claims, and timeline observations are not truncated mid-JSON.
  - In `backend/app/services/llm_client.py`:
    - Imported `LengthFinishReasonError` from `openai`.
    - Added dedicated exception handling in `call_structured` to catch `LengthFinishReasonError`, automatically increase `current_max_tokens` (by 1.5x up to 8192), and retry with a prompt instructing concise bullet points, making the extraction pipeline resilient against unexpected token overflow.
  - Restarted backend Uvicorn daemon on `0.0.0.0:8000`.
  - Ran full test suite (`pytest -v`), with all 24 unit and integration tests passing.
