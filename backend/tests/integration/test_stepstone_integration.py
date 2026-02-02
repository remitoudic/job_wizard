import pytest
from unittest.mock import AsyncMock, patch
from app.services.job_parser import JobParser

@pytest.mark.asyncio
async def test_stepstone_integration_parsing():
    # Mock specific Stepstone HTML response
    mock_html = """
    <html>
        <body>
            <h1 class="listing-job-title">Senior Developer</h1>
            <div data-at="header-company-name">Tech Corp</div>
            <div data-at="job-content">
                Build great things.
            </div>
        </body>
    </html>
    """
    
    # We mock the http client to avoid actual network calls (which might block or fail in CI)
    # checking that JobParser correctly delegates to StepStoneParser
    
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("app.services.job_parser.logfire") as mock_logfire:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        parser = JobParser()
        url = "https://www.stepstone.de/jobs--Senior-Developer--12345-inline.html"
        
        result = await parser.parse_url(url)
        
        assert result["title"] == "Senior Developer"
        assert result["company"] == "Tech Corp"
        assert "Build great things" in result["description"]
        assert result["source"] == "StepStone"
