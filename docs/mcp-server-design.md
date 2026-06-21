# Job Wizard MCP Server Design

## Overview
The Model Context Protocol (MCP) server allows external AI agents (like Gemini, cursor, or custom user agents) to securely interact with the Job Wizard system. This enables use cases where an agent can read an email (like a job rejection or interview invite) and automatically update the corresponding application status in Job Wizard.

## Architecture
- **Language**: Python (utilizing the official `mcp` SDK)
- **Integration**: Runs as a standalone stdio-based server script or SSE server that connects directly to the existing `job-wizard-db` (SQLModel).
- **Authentication**: External agents will need to authenticate, likely passing an API key or User ID as an environment variable or initialization parameter, ensuring they only modify their own data.

## Proposed Tools
The MCP server will expose the following tools to the LLMs:

### 1. `search_applications`
**Purpose**: Find an application ID based on company name, job title, or status.
**Parameters**:
- `company` (string, optional)
- `job_title` (string, optional)
- `status` (string, optional)
**Returns**: A list of matching applications (IDs, titles, companies, statuses).

### 2. `update_application_status`
**Purpose**: Update the status of an existing application.
**Parameters**:
- `application_id` (integer, required)
- `new_status` (string, required: 'APPLIED', 'REJECTED', 'INTERVIEWING', 'OFFER', etc.)
- `notes` (string, optional): Context for the update (e.g., "Received rejection email").
**Returns**: Success confirmation and updated application details.

### 3. `get_application_details`
**Purpose**: Get full details of a specific application.
**Parameters**:
- `application_id` (integer, required)

## Implementation Steps
1. Add `mcp` library to `pyproject.toml`.
2. Create `mcp_server.py` in `services/backend/app/`.
3. Implement database connection logic reusing the `database_pkg` models and engine.
4. Implement the `@mcp.tool()` handlers for the proposed tools.
5. Provide instructions for users on how to configure their external agent clients to connect to this script via `stdio`.
