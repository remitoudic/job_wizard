import sys
import hashlib
from sqlmodel import select, Session
from database_pkg import engine
from database_pkg.models import Application, ApplicationStatus, ApplicationStatusHistory
from database_pkg.models import JobDescription as DBJobDescription
from database_pkg.models.api_key import ApiKey
from mcp.server.fastmcp import FastMCP
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Initialize FastMCP server
mcp = FastMCP("Job Wizard")

# Context variable to store the authenticated user ID for the current request
mcp_user_id: ContextVar[int] = ContextVar("mcp_user_id")


class MCPAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow OPTIONS for CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                {
                    "error": "Unauthorized",
                    "detail": "Missing or invalid Authorization header",
                },
                status_code=401,
            )

        token = auth_header.split(" ")[1]
        key_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Verify token in database
        with Session(engine) as session:
            statement = select(ApiKey).where(ApiKey.key_hash == key_hash)
            api_key = session.exec(statement).first()

            if not api_key:
                return JSONResponse(
                    {"error": "Unauthorized", "detail": "Invalid API Key"},
                    status_code=401,
                )

            # Set the user ID in the context variable
            mcp_user_id.set(api_key.user_id)

            # Update last used
            from datetime import datetime, timezone

            api_key.last_used_at = datetime.now(timezone.utc)
            session.add(api_key)
            session.commit()

        # Proceed with the request
        return await call_next(request)


# Create the SSE App and add auth middleware
mcp_sse = mcp.sse_app()
mcp_sse.add_middleware(MCPAuthMiddleware)


@mcp.tool()
def search_applications(
    company: str = None, job_title: str = None, status: str = None
) -> str:
    """
    Search for a user's job applications. Use this to find the ID of an application.
    """
    try:
        user_id_int = mcp_user_id.get()
    except LookupError:
        return "Error: Could not determine authenticated user context."

    with Session(engine) as session:
        statement = (
            select(Application, DBJobDescription)
            .join(DBJobDescription)
            .where(Application.user_id == user_id_int)
        )

        if company:
            statement = statement.where(DBJobDescription.company.ilike(f"%{company}%"))
        if job_title:
            statement = statement.where(
                DBJobDescription.job_title.ilike(f"%{job_title}%")
            )
        if status:
            try:
                status_enum = ApplicationStatus(status)
                statement = statement.where(Application.status == status_enum)
            except ValueError:
                return f"Error: Invalid status. Must be one of: {[s.value for s in ApplicationStatus]}"

        results = session.exec(statement.limit(20)).all()

        if not results:
            return "No matching applications found."

        output = []
        for app, job_desc in results:
            output.append(
                f"ID: {app.id} | Company: {job_desc.company} | Title: {job_desc.job_title} | Status: {app.status.value}"
            )

        return "\n".join(output)


@mcp.tool()
def update_application_status(
    application_id: int, new_status: str, notes: str = None
) -> str:
    """
    Update the status of an application.
    new_status must be one of the valid application statuses (e.g., 'APPLIED', 'REJECTED', 'INTERVIEWING', 'OFFER').
    """
    try:
        user_id_int = mcp_user_id.get()
    except LookupError:
        return "Error: Could not determine authenticated user context."

    with Session(engine) as session:
        statement = select(Application).where(
            Application.id == application_id, Application.user_id == user_id_int
        )
        application = session.exec(statement).first()

        if not application:
            return f"Error: Application {application_id} not found or you don't have permission."

        try:
            status_enum = ApplicationStatus(new_status)
        except ValueError:
            return f"Error: Invalid status '{new_status}'. Must be one of: {[s.value for s in ApplicationStatus]}"

        history = ApplicationStatusHistory(
            application_id=application.id,
            old_status=application.status,
            new_status=status_enum,
            notes=notes if notes else "Status updated via MCP agent",
        )
        session.add(history)
        application.status = status_enum

        if notes:
            application.notes = (
                f"{application.notes}\n[{notes}]" if application.notes else notes
            )

        session.add(application)
        session.commit()

        return (
            f"Successfully updated application {application_id} to {status_enum.value}."
        )


if __name__ == "__main__":
    # If run directly without FastAPI, default to stdio but warn about auth
    print(
        "Warning: Running in stdio mode bypassing API Key auth. To use API Keys, mount mcp.sse_app in FastAPI.",
        file=sys.stderr,
    )
    mcp.run(transport="stdio")
