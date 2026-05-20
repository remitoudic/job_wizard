import pytest
from bs4 import BeautifulSoup
from app.services.cover_letter.job_parsers.wwr import WWRParser


@pytest.fixture
def parser():
    return WWRParser()


def test_normalize_url(parser):
    url = "https://weworkremotely.com/remote-jobs/company-job-title?source=rss"
    assert (
        parser.normalize_url(url)
        == "https://weworkremotely.com/remote-jobs/company-job-title"
    )


def test_extract_job_data_success(parser):
    html = """
    <html>
        <body>
            <div class="listing-header-container">
                <h1>Senior Python Developer</h1>
                <div class="company-card">
                    <h2>Acme Remote Corp</h2>
                </div>
            </div>
            <div id="job-listing-show-container">
                <p>We are looking for a developer.</p>
                <br>
                <ul>
                    <li>Python</li>
                    <li>Django</li>
                </ul>
                <div class="apply_tooltip">
                    <a href="#">Apply</a>
                </div>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    data = parser.extract_job_data(soup, "https://weworkremotely.com/job")

    assert data["title"] == "Senior Python Developer"
    assert data["company"] == "Acme Remote Corp"
    assert "We are looking for a developer." in data["description"]
    assert "Apply" not in data["description"]  # Button should be removed
    assert data["source"] == "WeWorkRemotely"


def test_extract_job_data_fallback(parser):
    html = """
    <html>
        <body>
            <h1>Fallback Title</h1>
            <div id="job-listing-show-container">
                Description text
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    data = parser.extract_job_data(soup, "https://weworkremotely.com/job")

    assert data["title"] == "Fallback Title"
    assert data["company"] == "Unknown Company"
    assert data["description"] == "Description text"
