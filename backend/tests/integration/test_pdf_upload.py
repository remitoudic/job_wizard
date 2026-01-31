from fastapi.testclient import TestClient
from app.main import app
from reportlab.pdfgen import canvas
import io

client = TestClient(app)

def create_dummy_pdf_bytes():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "CURRICULUM VITAE")
    c.drawString(100, 730, "Name: Test Applicant")
    c.drawString(100, 710, "Skills: Python, FastAPI, Svelte")
    c.drawString(100, 690, "Experience: 5 years of experience in building web applications.")
    c.save()
    buffer.seek(0)
    return buffer.read()

def create_dummy_image_bytes():
    # minimalist 1x1 GIF
    return b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

def test_upload_context():
    pdf_content = create_dummy_pdf_bytes()
    
    response = client.post(
        "/api/upload-context",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "text" in data
    assert "Test Applicant" in data["text"]

def test_upload_invalid_file():
    response = client.post(
        "/api/upload-context",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400

def test_upload_image_regression():
    img_content = create_dummy_image_bytes()
    response = client.post(
        "/api/upload-image",
        files={"file": ("test.gif", img_content, "image/gif")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "url" in data

# We mock LLM service to avoid needing actual Ollama for this unit/integration test logic
# because calling real Ollama is slow and might fail if model not pulled.
# But if we want to test the *arguments* passing, we can mock the method.
from unittest.mock import patch, AsyncMock  # noqa: E402

@patch("app.services.llm_service.LLMService.generate_cover_letter", new_callable=AsyncMock)
def test_generate_cover_letter_with_context(mock_generate):
    mock_generate.return_value = ("Dear Hiring Manager, this is a generated letter.", "MockSource", "mock-alt-id")
    
    response = client.post(
        "/api/generate-cover-letter",
        json={
            "job_description": {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "description": "We need a dev.",
                "requirements": ["Python", "FastAPI"],
                "url": "http://example.com"
            },
            "user_name": "Test User",
            "context_text": "My CV Context info"
        }
    )
    
    assert response.status_code == 200
    assert mock_generate.called
    # storage of arguments verify that context_text was passed
    kwargs = mock_generate.call_args.kwargs
    assert kwargs["context_text"] == "My CV Context info"
