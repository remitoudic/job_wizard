import pytest
from bs4 import BeautifulSoup
from app.services.parsers.arbeitnow import ArbeitnowParser

@pytest.fixture
def parser():
    return ArbeitnowParser()

def test_normalize_url(parser):
    url = "https://www.arbeitnow.com/jobs/slug?utm_source=test"
    assert parser.normalize_url(url) == "https://www.arbeitnow.com/jobs/slug"

def test_extract_job_data_json_ld(parser):
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "title": "Senior Engineer",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Tech Corp"
                },
                "description": "<p>Great job</p>"
            }
            </script>
        </head>
        <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    data = parser.extract_job_data(soup, "https://www.arbeitnow.com/jobs/test")
    
    assert data["title"] == "Senior Engineer"
    assert data["company"] == "Tech Corp"
    assert "Great job" in data["description"]
    assert data["source"] == "Arbeitnow"

def test_extract_job_data_fallback(parser):
    html = """
    <html>
        <body>
            <h1>Junior Dev</h1>
            <div itemprop="hiringOrganization">Small Startup</div>
            <div itemprop="description">Write code</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    data = parser.extract_job_data(soup, "https://www.arbeitnow.com/jobs/test")
    
    assert data["title"] == "Junior Dev"
    assert data["company"] == "Small Startup"
    assert "Write code" in data["description"]
