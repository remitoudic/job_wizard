# Feature Spec: Admin Dashboard Improvements

## 1. Description
The Admin Space in Job Wizard currently provides a read-only view of registered users. To give administrators the necessary tools to monitor, maintain, and control the system, we will upgrade the Admin Dashboard into an interactive operational center.

This enhancement introduces:
1. **User Management Module**: An administrative form and controls to create new users, set roles (User vs. Admin), and perform basic management actions.
2. **System Health Check Area**: A real-time diagnostic panel displaying the connectivity, response latency, and operational status of all key infrastructure components (Temporal.io, Ollama, Database, Backend Server, and Cloud providers).
3. **Tabbed Navigation (Slider/Switcher)**: A premium, sliding/tabbed interface to seamlessly switch between the User Management and System Health monitoring sections.

---

## 2. Specifications

### A. Frontend Layout & Navigation
- **Navigation Switcher**: A modern horizontal slider/tab switcher at the top of the Admin page. It allows the admin to toggle between:
  - **Users**: User table + "Create New User" button/modal.
  - **System Health**: Health status cards for infrastructure services.
- **Visual Design**: Sleek card-based layout using the application's Tailwind-based styling guidelines, featuring clear color coding for service health (e.g., green for healthy, orange/yellow for warnings, red for offline/error).

### B. User Management Section
- **Create User Interface**:
  - A "+ New User" button that opens a clean modal or slide-over form.
  - Form Fields:
    - First Name (String, Required)
    - Surname (String, Required)
    - Email (Email, Required, Unique)
    - Username (String, Required, Unique)
    - Password (Password, Required)
    - Role (Select dropdown: "User" or "Admin/Superuser")
- **User List Table Expansion**:
  - Display user details including Username, Email, Full Name, Last Login timestamp, and Role badge.
  - Add an action column with future hooks for "Edit", "Deactivate", or "Reset Password" (placeholder actions for Phase 1).

### C. System Health Section
- **Infrastructure Status Checks**:
  - **Backend Server**: Checks if the API is reachable and returns HTTP 200.
  - **Database**: Runs a fast `SELECT 1` query to check PostgreSQL/DB connection latency.
  - **Ollama (LLM Provider)**: Pings Ollama endpoint, verifies if the configured model is available/ready.
  - **Temporal.io**: Connects to the Temporal Client and verifies if the Temporal service port is reachable.
  - **Cloud/External Services**: Verifies connectivity for Cloudinary, Groq, OpenRouter, and LlamaCloud APIs.
- **Health Panel Design**:
  - Grid of status cards.
  - Each card shows:
    - Service Name
    - Status Indicator (Icon + Status label: `Healthy` / `Degraded` / `Offline` / `Skipped`)
    - Latency (in milliseconds, where applicable)
    - Configuration Metadata (e.g., host url, model name, namespace)
    - Error details (if any)
  - A manual "Refresh Diagnostics" button to re-trigger health checks.

### D. Backend APIs
- **Admin User Creation Endpoint**:
  - `POST /api/users/` (restricted to superusers).
  - Accepts full user creation details (email, username, password, first name, surname, and `is_superuser`).
- **Secure Health Endpoint**:
  - Upgrade or wrap `/api/debug/health` to enforce `get_current_superuser` authorization to prevent leaking infrastructure details, latency, and API keys to standard users.
  - Add `temporal` connectivity verification in the response.

---

## 3. Validation Criteria

### Automated Verification
- **Backend Tests**:
  - Unit tests verifying `POST /api/users/` fails for non-superusers.
  - Integration tests verifying `POST /api/users/` successfully inserts a user into the DB with standard and superuser roles.
  - Unit tests verifying the system health check logic handles offline services gracefully (returning status: "error") without crashing the endpoint.
- **Frontend Tests**:
  - Verification that the navigation switcher toggles Svelte UI sections correctly.
  - Verification that the "Create User" form performs basic validation (required fields, email format).

### Manual Verification
1. **Security Access Gate**: Log in as a regular user, navigate to `/admin`, and verify that the app redirects to `/` and blocks access. Verify that sending direct API requests to `/api/users/` or `/api/debug/health` returns `403 Forbidden` or `401 Unauthorized` for regular users.
2. **Dashboard Navigation**: Log in as a superuser, navigate to `/admin`, and verify that the layout displays the slider/switcher. Verify that clicking "System Health" hides the user table and displays the diagnostics panel.
3. **User Creation Flow**: Click "+ New User", fill in the form with a new user's details (both with/without the "Admin" role selected), click "Submit", and verify that the modal closes, the user appears in the user list, and can successfully log in using the credentials.
4. **Service Outage Simulation**: Stop the local Ollama instance (or point `OLLAMA_HOST` to an invalid port in env), refresh the diagnostics panel, and verify that the Ollama card turns red and displays a descriptive connection error, while the database and backend cards remain green.
