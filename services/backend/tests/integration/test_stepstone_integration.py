import pytest
from unittest.mock import patch
from app.services.cover_letter.job_parsers.job_parser import JobParser


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

    # Mock StepStoneParser.fetch_content to avoid curl_cffi network calls
    with patch(
        "app.services.cover_letter.job_parsers.stepstone.StepStoneParser.fetch_content",
        return_value=mock_html,
    ) as mock_fetch:
        parser = JobParser()
        url = "https://www.stepstone.de/jobs--Senior-Developer--12345-inline.html"

        result = await parser.parse_url(url)

        assert result["title"] == "Senior Developer"
        assert result["company"] == "Tech Corp"
        assert "Build great things" in result["description"]
        assert result["source"] == "StepStone"

        # Verify fetch_content was called
        mock_fetch.assert_called_once_with(url)
