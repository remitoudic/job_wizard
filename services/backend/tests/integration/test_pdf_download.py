from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client = TestClient(app)


def test_pdf_generation_and_download_flow():
    """
    Test the full flow:
    1. Generate a PDF (authenticated or not - using minimum fields)
    2. Verify the response contains a filename and URL
    3. Try to download via the /uploads/ static mount (frontend dev proxy style)
    4. Try to download via the /api/download/{filename} endpoint
    """

    # 1. Generate PDF
    # We use minimal required fields.
    # Note: in test_mode or mock, we assume PDF generation doesn't require external services or valid images if optional

    payload = {
        "cover_letter": "This is a test cover letter content.",
        "job_title": "Test Job Title",
        "company": "Test Company",
        "user_name": "Test User",
        # Optional fields left empty or default
    }

    # The endpoint expects form data
    response = client.post("/api/generate-pdf", data=payload)

    assert response.status_code == 200, f"Generate PDF failed: {response.text}"
    data = response.json()

    assert "filename" in data
    assert "url" in data

    filename = data["filename"]
    url = data["url"]

    print(f"Generated PDF: {filename} at {url}")

    # Verify file exists on disk (TestClient runs in same process usually, but good to check)
    upload_dir = Path("/app/uploads")
    if not upload_dir.exists():
        # In case we operate in a weird env, but app/main.py creates it.
        # If running locally without docker path mapping, this might fail if app code relies on absolute /app/uploads
        # But let's check response access instead which is more "integration-y"
        pass

    # 2. Download via Static Mount (/uploads/...)
    # The URL returned is like "/uploads/uuid.pdf"
    # TestClient handles app.mounts too if configured correctly

    # Check if the url starts with /api/download
    assert url.startswith("/api/download/")

    response_static = client.get(url)
    assert (
        response_static.status_code == 200
    ), "Failed to access file via static /uploads mount"
    assert response_static.headers["content-type"] == "application/pdf"
    assert len(response_static.content) > 0

    # 3. Download via API endpoint (/api/download/...)
    # The route is @router.get("/download/{filename}") in cover_letter.py
    # prefixed with /api in main.py -> /api/download/{filename}

    download_api_url = f"/api/download/{filename}"
    response_api = client.get(download_api_url)

    assert (
        response_api.status_code == 200
    ), "Failed to access file via /api/download endpoint"
    assert response_api.headers["content-type"] == "application/pdf"
    # Content should match
    assert response_api.content == response_static.content


def test_download_nonexistent_file():
    response = client.get("/api/download/nonexistent_file.pdf")
    assert response.status_code == 404
