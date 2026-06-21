# End-to-End (E2E) Testing the Job Wizard MCP Server

This document outlines the testing journey for the Job Wizard Model Context Protocol (MCP) server.

When building an MCP server, testing is unique because the "client" isn't a human clicking a UI, but an AI Agent deciding which tools to call. Therefore, our E2E testing journey is broken into two phases:
1. **The Developer Journey (Inspector)**: Ensuring the server starts, tools are registered, and they execute against the database correctly.
2. **The Agent Journey (Gemini / Real LLM)**: Ensuring the LLM understands the tool descriptions and can autonomously chain tools together based on natural language prompts.

---

## Phase 1: The Developer Journey (MCP Inspector)

Before hooking up a real AI, we need to ensure the raw mechanics of the `stdio` transport and the JSON-RPC messages work. We use the official `@modelcontextprotocol/inspector` for this. It acts as a simulated, manual agent.

### Prerequisites
- Node.js and `npx` installed.
- Your Job Wizard python virtual environment configured (`uv`).
- A valid `JOB_WIZARD_USER_ID` from your database (e.g., `1`).

### Steps
1. **Start the Inspector**
   Run the following command from the `services/backend` directory:
   ```bash
   JOB_WIZARD_USER_ID=1 npx @modelcontextprotocol/inspector uv run python app/mcp_server.py
   ```

2. **Access the UI**
   Open your browser to the URL provided in the terminal (usually `http://localhost:5173`).

3. **Verify Tool Registration**
   In the Inspector UI, ensure both `search_applications` and `update_application_status` appear in the Tools list. If they do, the MCP protocol handshake was successful.

4. **Execute `search_applications`**
   - Click on the `search_applications` tool.
   - Enter a mock payload, for example: `{"company": "Google"}`.
   - Click **Execute**.
   - **Expected Result**: You should see a successful JSON response containing application IDs from the database.

5. **Execute `update_application_status`**
   - Take an Application ID from the previous step (e.g., `123`).
   - Click the `update_application_status` tool.
   - Enter the payload: `{"application_id": 123, "new_status": "REJECTED", "notes": "E2E Test Update"}`.
   - Click **Execute**.
   - **Expected Result**: A success message. Verify in your Job Wizard web UI or database that the status changed and the history log was created.

---

## Phase 2: The Agent Journey (Real LLM Testing)

Once the raw tools work, we must test the "semantic" layer. Does the AI understand *when* and *how* to use the tools based on unstructured text (like a forwarded email)?

We will use a Gemini-powered Agent client as our test agent.

### Configuration
1. Open your Gemini Agent configuration or IDE settings that support MCP integrations (e.g., `mcp_servers.json` or your specific desktop client).
2. Add the Job Wizard server configuration:
   ```json
   {
     "mcpServers": {
       "job-wizard": {
         "command": "uv",
         "args": [
           "run",
           "python",
           "/absolute/path/to/job_wizard/services/backend/app/mcp_server.py"
         ],
         "env": {
           "JOB_WIZARD_USER_ID": "1"
         }
       }
     }
   }
   ```
3. Restart your Gemini client.

### The Testing Scenario
To test the full loop, open a new chat in your Gemini client and paste a mock email:

> "Hey Gemini, I just got this email, can you update my job tracker accordingly?
>
> *Hi Remi, Thank you for applying to the Software Engineer role at Acme Corp. Unfortunately, we have decided to move forward with other candidates at this time...*"

### Expected Agent Behavior
Watch Gemini's response. A successful E2E test will look like this:
1. Gemini parses the text and identifies "Acme Corp" and a "Rejection".
2. Gemini autonomously decides to use the `search_applications` tool with `{"company": "Acme Corp"}` to find the specific application ID.
3. Gemini reads the result, extracts the `application_id`.
4. Gemini autonomously uses the `update_application_status` tool with the ID, changing the status to `REJECTED`, and perhaps adding the email snippet as `notes`.
5. Gemini replies to you: *"I've successfully updated your application at Acme Corp to Rejected."*

If the agent successfully performs this chain of actions without asking you for the application ID, your E2E test is completely successful!
