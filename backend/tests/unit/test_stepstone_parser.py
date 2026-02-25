import pytest
from bs4 import BeautifulSoup
from app.services.job_parsers.stepstone import StepStoneParser

@pytest.fixture
def parser():
    return StepStoneParser()

@pytest.fixture
def sample_html():
    return """
    <html>
        <head>
            <title>Software Engineer (m/f/d) - Job at Veli in Kassel</title>
        </head>
        <body>
            <div data-at="header-job-title">Software Engineer (m/f/d)</div>
            <a class="listing-content-provider-1">Veli</a>
            <div class="js-app-ld-ContentBlock">
                <p>We are looking for a Software Engineer.</p>
                <br>
                <p>Requirements: Python, Svelte.</p>
            </div>
        </body>
    </html>
    """

def test_normalize_url(parser):
    url = "https://www.stepstone.de/jobs--Software-Engineer-m-f-d-Kassel-Veli--13072528-inline.html?rltr=ma_rj_0_0_0_0_0"
    expected = "https://www.stepstone.de/jobs--Software-Engineer-m-f-d-Kassel-Veli--13072528-inline.html"
    assert parser.normalize_url(url) == expected

def test_extract_job_data(parser, sample_html):
    url = "https://www.stepstone.de/test-job"
    soup = BeautifulSoup(sample_html, "lxml")
    
    data = parser.extract_job_data(soup, url)
    
    assert data["title"] == "Software Engineer (m/f/d)"
    assert data["company"] == "Veli"
    assert "We are looking for a Software Engineer" in data["description"]
    assert "Python, Svelte" in data["description"]
    assert data["url"] == url
    assert data["source"] == "StepStone"

def test_extract_job_data_fallback(parser):
    # Test fallback selectors or missing data
    html = """
    <html>
        <head><title>Fallback Job Title | Stepstone</title></head>
        <body>
            <div class="listing-org-name">Fallback Company</div>
            <div class="job-ad-container">
                Fallback Description
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    data = parser.extract_job_data(soup, "http://test.url")
    
    assert data["title"] == "Fallback Job Title"
    assert data["company"] == "Fallback Company"
    assert data["description"] == "Fallback Description"

def test_extract_job_data_json_ld(parser):
    # Test JSON-LD extraction without specific HTML selectors
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org/",
                "@type": "JobPosting",
                "title": "JSON-LD Engineer",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Structured Data Co."
                },
                "description": "<p>We need structured data.</p><p>Requirements: JSON.</p>",
                "datePosted": "2023-01-01"
            }
            </script>
        </head>
        <body>
            <div class="messy-html">
                Some unstructured content that shouldn't be picked up.
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    data = parser.extract_job_data(soup, "http://test.url")
    
    assert data["title"] == "JSON-LD Engineer"
    assert data["company"] == "Structured Data Co."
    assert "We need structured data." in data["description"]
    assert "Requirements: JSON." in data["description"]
    assert data["source"] == "StepStone"
