# Feature Spec: LLM Model Inference Health Check

## 1. Description
While existing connectivity diagnostics check if LLM provider endpoints (Ollama, Groq, OpenRouter) are reachable and whether credentials are syntactically valid, they do not verify if the target models are capable of generating responses. An API key might be valid, but model requests can still fail due to:
- Insufficient credits or account limits.
- Rate limits.
- The requested model not being pulled, supported, or found.
- Content filtering or validation errors.

This feature introduces an **Active Inference Health Check** for Ollama, Groq, and OpenRouter. It performs a lightweight text generation (completion) call using a tiny prompt (`ping`) with `max_tokens=1` to verify if model generation is fully operational. If the generation fails, it captures the exact API error message and displays it to the administrator in the Admin Space.

---

## 2. Specifications

### A. Backend Diagnostics Update (`/api/debug/health`)
- **Ollama Inference Test**:
  - Perform an async `client.generate` call using the configured `OLLAMA_MODEL`.
  - Limit generation tokens (`num_predict=1`) to keep execution instant.
  - If it fails, capture the exception string.
- **Groq Inference Test**:
  - Send a `POST` request to `https://api.groq.com/openai/v1/chat/completions`.
  - Pass the configured `GROQ_MODEL_1`, a prompt `[{"role": "user", "content": "ping"}]`, and `max_tokens=1`.
  - If the status code is not 200, parse the JSON error payload: `response.json()["error"]["message"]`.
- **OpenRouter Inference Test**:
  - Send a `POST` request to `https://openrouter.ai/api/v1/chat/completions`.
  - Pass the configured `OPENROUTER_MODEL`, a prompt `[{"role": "user", "content": "ping"}]`, and `max_tokens=1`.
  - If the status code is not 200, parse the JSON error payload: `response.json()["error"]["message"]`.
- **Response Structure**:
  Update `/api/debug/health` output structure to include:
  ```json
  {
    "ollama": {
      "status": "ok",
      "inference_status": "ok" | "error",
      "inference_error": "..."
    },
    "providers": {
      "groq": {
        "status": "ok" | "error" | "skipped",
        "inference_status": "ok" | "error" | "skipped",
        "inference_error": "..."
      },
      "openrouter": {
        "status": "ok" | "error" | "skipped",
        "inference_status": "ok" | "error" | "skipped",
        "inference_error": "..."
      }
    }
  }
  ```

### B. Frontend UI Additions (`/admin`)
- **Ollama Diagnostic Card**:
  - Add an **Inference Test** line.
  - Show a green badge `Passed` if `inference_status == 'ok'`.
  - Show a red badge `Failed` if `inference_status == 'error'`, along with the error message below it.
- **Cloud Providers Diagnostic Card**:
  - For both Groq and OpenRouter:
    - Display **Inference**:
      - `Passed` (green badge) if `inference_status == 'ok'`.
      - `Failed` (red badge) if `inference_status == 'error'`.
      - `Skipped` (gray badge) if `inference_status == 'skipped'`.
    - If `Failed`, render a tooltip or text element with the exact error message (e.g. *"Insufficient funds"*, *"Rate limit exceeded"*).

### C. Global Admin Alerts & Tab Switcher Indicator
- **Initial Fetch**: Trigger the system health check on page mount (`onMount`) rather than waiting for the administrator to click the "System Health" tab. This ensures the frontend knows the system status immediately.
- **Tab Switcher Alert**: Next to the "System Health" button in the sliding switcher, render a red notification dot/badge (`animate-ping`) if any critical service check fails.
- **Global Error Banner**: If any model inference check (or database/temporal connection) fails, display a prominent warning banner at the top of the Admin Control Center, showing the list of failed services (e.g. *"System Alert: Ollama LLM, Groq LLM failed inference checks. Please review the System Health tab."*). This banner is visible regardless of the active tab.

---

## 3. Validation Criteria

### Automated Verification
- **Integration Tests**:
  - Write test cases in `services/backend/tests/integration/test_admin.py` to:
    - Verify that a successful generation test returns `inference_status: "ok"`.
    - Verify that a failed model test returns `inference_status: "error"` and the parsed error message.

### Manual Verification
1. **Ollama Normal Operation**: With local Ollama running and the configured model pulled, verify that the Ollama card in the Admin Space shows `Inference Test: Passed`.
2. **Ollama Model Missing**: Set `OLLAMA_MODEL` in `.env` to a non-existent model name, restart the containers, refresh the diagnostics, and verify that the Ollama card shows `Inference Test: Failed` with the error message `model not found`.
3. **Groq Credit Check**: Set a dummy key for `GROQ_API_KEY` in `.env`, refresh diagnostics, and verify that the Groq provider shows `Inference: Failed` with the parsed message *"Invalid API Key"*.
4. **OpenRouter Error Check**: Simulate an OpenRouter outage or quota error, and verify that the exact error returned by OpenRouter's API is displayed to the admin.
5. **Global Visibility Check**: While on the default **Users** tab with a failed model check, verify that a red banner is displayed at the top of the Admin page showing the failed services and a link to switch to the System Health tab. Verify that a red notification dot is pulsing on the "System Health" switcher button.
