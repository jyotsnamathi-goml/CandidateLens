# IDE Changes: 004 - Live Key Verification & Minimal Token Smoke Test

## Summary
- Verified the newly configured OpenAI API key with `LLM_MOCK=false`.
- Identified and fixed a Python 3.13 / Windows `httpx2` decompression bug by explicitly configuring `OpenAI(..., http_client=httpx.Client(timeout=60.0))` in `backend/app/services/llm_client.py`.
- Conducted a single minimal structured live test against `gpt-4o-mini` (`jd_parsing` stage):
  - Tokens: 227 input tokens, 198 output tokens.
  - Latency: 3,627 ms.
  - Measured Cost: $0.000153 USD (~0.015 cents).
  - Schema validation: Pydantic `JDParsingResult` validated and returned successfully.
  - Call recorded accurately in SQLite `llm_calls` table with `mock=False`.
- Updated `backend/tests/conftest.py` to ensure automated pytest runs always set `LLM_MOCK=True`, keeping all 24 unit tests completely free (zero token spend) and passing offline in <1.5s.
