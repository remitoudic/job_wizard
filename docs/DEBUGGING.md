# Vite a Job! Debugging Guide

This guide covers advanced diagnostic techniques and tools for the Vite a Job! observability stack.

---

## 🔍 1. Real-time Service Health
We use a centralized diagnostic endpoint to verify backend connectivity.

### The Diagnostic Endpoint
Access `GET /api/debug/health` (requires authentication) to see the status of all critical services.

**Sample Response:**
```json
{
  "database": {
    "status": "ok",
    "latency_ms": 1.25,
    "pubsub": "active"
  },
  "ollama": {
    "status": "ok",
    "latency_ms": 45.32,
    "host": "http://ollama:11434",
    "configured_model": "qwen2:0.5b",
    "model_ready": true
  },
  "providers": {
    "groq": { "status": "ok", "latency_ms": 120.5 },
    "openrouter": { "status": "ok", "latency_ms": 210.8 }
  },
  "cloudinary": {
    "status": "ok",
    "latency_ms": 85.2
  },
  "llamacloud": {
    "status": "ok",
    "latency_ms": 142.1
  }
}
```

### What to check:
- **`database.pubsub`**: Must be `active`. If it shows `down`, the background listener task has crashed, and real-time UI updates will fail.
- **`ollama.model_ready`**: If `false`, the backend can reach Ollama, but the model hasn't been pulled. Run `docker exec jobwizard-ollama ollama pull <model_name>`.
- **`providers.*.status`**: If `error` or `401`, check your API keys in the `.env` file.
- **`cloudinary.status`**: If `error`, check your `CLOUDINARY_URL`. Ensure it includes the cloud name, API key, and secret.
- **`llamacloud.status`**: If `error`, the CV parser will fail. Check your `LLAMA_CLOUD_API_KEY`.

---

## 🖼️ 3. Profile Pictures & Cloudinary
We use Cloudinary for hosted storage of user profile pictures and CV documents.

### Common Issues:
- **Upload Timeout**: Usually caused by huge files or network latency.
- **"Invalid Signature"**: Check if your system clock is in sync, as Cloudinary uses timestamps for signing requests.
- **Missing Images**: If the DB has a URL but the image doesn't load, verify that the `public_id` hasn't changed or been deleted via the Cloudinary Media Library.

### Manual Verification:
```bash
# Check if the Cloudinary URL is loaded correctly in the backend
docker exec jobwizard-backend-prod env | grep CLOUDINARY_URL
```

---

## 📄 4. CV Parsing & LlamaCloud
Parsing is an asynchronous two-step process: Extraction (LlamaParse) → Structuring (Groq LLM).

### The Parsing Flow:
1. User uploads PDF.
2. Backend sends PDF to **LlamaCloud**.
3. LlamaCloud returns Markdown.
4. Backend sends Markdown to **Groq** to extract a JSON schema.

### Troubleshooting "Stuck" CVs:
- Check the **LlamaCloud Dashboard** to see if the file is still being processed.
- Monitor backend logs for `LlamaParse failed` or `Structuring failed`.
- Use **Logfire** to track the duration of the `parse_pdf` span. Groq structuring usually takes 2-5 seconds.

---

## 🪵 2. Observability with Logfire
We use [Pydantic Logfire](https://logfire.pydantic.dev/) for deep tracing of asynchronous tasks, specifically the "Race Mode" generation.

### Visualizing the Race
In the Logfire dashboard, look for **"Generate Cover Letter"** spans.
- **Nested Spans**: Every agent run (Ollama vs. Groq) appears as a child span.
- **Concurrency**: Parallel bars indicate that models are truly running in "Race Mode".
- **Token Usage**: Click on an "Agent Generation" span to see `request_tokens`, `response_tokens`, and `total_tokens`.

### Tracking Failovers
Search for logs with the attribute `event="Provider Rate Limit"`. This tells you exactly when a secondary provider (OpenRouter) took over because the primary (Groq) was rate-limited.

---

## 📡 3. Debugging Asynchronous Flows
Vite a Job! uses a **Persistence-First** notification model.

### Checking Job Status
If a generation task appears "stuck" in the UI:
1. Check the `JobStatus` table in the database:
   ```bash
   docker exec -it jobwizard-postgres psql -U jobwizard -d jobwizard
   SELECT job_id, status, updated_at FROM jobstatus ORDER BY updated_at DESC LIMIT 5;
   ```
2. If the status in the DB is `completed` but the UI is still loading, the issue is likely with the **Server-Sent Events (SSE)** connection or the **Pub/Sub** listener.

### Client-Side Verification (Browser)
If you aren't seeing updates:
1. Open Chrome DevTools → **Network** tab.
2. Find the request to `/api/generate-cover-letter/stream`.
3. Check the **EventStream** tab within that request.
4. You should see JSON "data" chunks arriving in real-time. If there is no "stream" request, the frontend failed to initiate the listener.

### Pub/Sub Troubleshooting
Verify that notifications are being broadcast:
```bash
# In one terminal, listen to the channel
docker exec -it jobwizard-postgres psql -U jobwizard -d jobwizard -c "LISTEN cover_letter_notifications;"
```

---

## 🚨 4. Common Failure Modes

### 1. SSE Connection Timeouts
**Symptoms**: UI stuck on "Extracting..." or "Generating..." but backend logs show a winner.
**Cause**: The browser or a proxy (like Nginx) might be killing long-lived connections.
**Fix**: Our "Replay" logic should auto-sync the state on reconnect. Check `services/backend/app/api/routes/cover_letter.py` if replay is failing.

### 2. Ollama "Race" Failures
**Symptoms**: Only one model ever wins, or generation is extremely slow.
**Check**:
- Is `OLLAMA_HOST` reachable from the backend container?
- Is the Ollama container hitting CPU limits? (Check `docker stats`).

### 3. Database NOTIFY Payload Limits
PostgreSQL `NOTIFY` has a payload limit of **~8000 bytes**.
**Fix**: We keep notification payloads small (status only) and fetch large data (like the final letter) via standard GET requests if necessary.

---

## 🏹 5. Useful Debugging Commands

```bash
# View backend spans in real-time (if log-level is DEBUG)
docker compose logs -f backend | grep -i "span"

# Manually trigger a health check via curl
curl -H "Authorization: Bearer <YOUR_TOKEN>" http://localhost:8000/api/debug/health

# Verify Logfire connection
docker exec jobwizard-backend-prod python -c "import logfire; print(logfire.verify_token())"

# List all prompt audit logs (debug-only)
docker exec jobwizard-backend-prod ls -lh /app/logs/prompt_audit/
```

---

## 🏹 6. Advanced Logfire Tips
- **Search by Trace ID**: If a user reports an error, look for the `trace_id` in the frontend console and paste it into the Logfire search bar.
- **Environment Check**: Ensure `LOGFIRE_TOKEN` is present in your `.env.production`. Without it, spans will be logged locally but won't appear in the dashboard.

---

## 🏛️ 7. Prompt Audit Logs (Hallucinations)
When the AI model returns malformed data (hallucinations) that fail Pydantic validation, we save the **raw, unparsed output** to local files for debugging.

### How to use:
1. Identify a parsing failure in the logs (`CV Parsing (Validation)` or `Contact Extraction`).
2. Go to `/app/logs/prompt_audit/` inside the backend container.
3. Find the file with the matching timestamp.
4. Read the file to see the prompt context, the error message, and the exact raw text the model returned.

### Example Log Structure:
```text
=== PROMPT AUDIT LOG ===
Timestamp: 2026-04-07T07:44:00.123
Model: llama3.2:1b
Context/Source: CV Parsing (Pydantic Validation)

=== VALIDATION ERROR ===
1 validation error for CVData
experiences
  value is not a valid list

=== RAW LLM OUTPUT ===
"I am a software engineer with 5 years experience..." (Wait, this isn't JSON!)

=== END OF LOG ===
```
This is the fastest way to refine your prompts when the model "goes off the rails."
