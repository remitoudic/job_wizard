# Feature Spec: Magic Link User Invitations & Email Integration

## 1. Description
When administrators create new users in the Admin Control Center, requiring them to define a password manually poses security and convenience issues. This feature introduces a secure **Self-Service Invitation Flow** (Option B):

1. **Email Integration**: Adds a local mock SMTP mail catcher (**Mailpit**) in the development environment and SMTP configuration hooks in production.
2. **Magic Invitation Links**: The administrator provides only the user's name and email. The backend creates the user with a locked, random password, generates a secure password-reset token, and emails an invitation containing a "magic link" to the user.
3. **Password Setup Form**: Clicking the magic link opens a frontend form where the new user sets their own secure password, enabling them to log in for the first time.

---

## 2. Specifications

### A. Infrastructure & Email Server Config
- **Development**: Run `axllent/mailpit` in Docker Compose (SMTP port 1025, Web UI port 8025) to catch outgoing emails locally.
- **Production**: Route to an external transactional email provider (SendGrid, Mailgun, AWS SES) using standard environment variables:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASSWORD`
  - `SMTP_FROM`
  - `FRONTEND_URL` (to build the absolute invitation link)

### B. Backend JWT & Endpoints
- **JWT Helper**: Create a secure token with a 24-hour expiration containing the claims:
  - `sub`: the user's email
  - `action`: `"reset_password"`
- **Admin User Creation (`POST /api/users/`)**:
  - Accept optional password. If none is supplied, generate a strong random hash.
  - Accept `send_invite` boolean. If true, generate the JWT token and trigger an SMTP email asynchronously containing the magic link: `{FRONTEND_URL}/reset-password?token={TOKEN}`.
- **Token Verification (`POST /api/auth/reset-password/verify`)**:
  - Open endpoint accepting `{ "token": "..." }`.
  - Validate expiration, signature, and reset action. Returns `{ "email": "..." }` on success.
- **Password Confirm (`POST /api/auth/reset-password/confirm`)**:
  - Open endpoint accepting `{ "token": "...", "password": "..." }`.
  - Validate token, hash the new password, and update the database user record, clearing any placeholder credentials.

### C. Frontend Svelte Pages
- **Admin Modal Update (`/admin`)**:
  - Add a **"Send invitation email to set password"** checkbox (checked by default).
  - Bind the checkbox to hide the **Password** input field when checked, making it optional.
- **Password Set Form (`/reset-password`)**:
  - Create a new public route `/reset-password` that reads the `token` URL query parameter.
  - On mount, call the backend verification endpoint. If the token is invalid or expired, display a clear warning: *"This invitation link is invalid or has expired. Please contact your administrator."*
  - Display a card containing:
    - Target email address (read-only)
    - "New Password" input (password visibility togglable, minimum 6 characters)
    - "Confirm Password" input
    - "Set Password" submit button
  - On submit, call the confirm endpoint, display a success toast, and redirect to `/login` after a brief delay.

---

## 3. Validation Criteria

### Automated Verification
- **Unit & Integration Tests**:
  - Test `POST /api/users/` creates user with a random password when password is empty and `send_invite=True`.
  - Test `POST /api/auth/reset-password/verify` returns 200 and the correct email for a valid token.
  - Test `POST /api/auth/reset-password/verify` returns 400/401 for an expired or tampered token.
  - Test `POST /api/auth/reset-password/confirm` successfully updates the password in the database and verifies the user can log in with the new credentials.

### Manual Verification
1. **Admin Invitation Setup**: Navigate to `/admin` as an administrator, click "+ New User", check the "Send invitation email" box, fill in the email as `newmember@example.com`, and submit.
2. **Mail Capture Check**: Navigate to the local Mailpit dashboard at `http://localhost:8025`. Verify that a new email titled *"Welcome to Job Wizard — Set Your Password"* has arrived for `newmember@example.com`.
3. **Invitation Link Click**: Click the reset link in the Mailpit inbox. Verify that it opens `/reset-password` and displays the email `newmember@example.com` correctly.
4. **Token Expiry Validation**: Try modifying the URL token parameter (e.g. truncate characters) or test with an expired token. Verify the page displays an error and blocks password submission.
5. **Credentials Verification**: Enter a valid password, submit the form, verify that it redirects to `/login`, and check that the user can successfully log in using the newly created password.
