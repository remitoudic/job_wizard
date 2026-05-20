import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.cover_letter.job_parsers.indeed import IndeedParser
from app.services.cover_letter.job_parsers.registry import ParserRegistry


async def test_indeed():
    parser = IndeedParser()

    # 1. Test Normalization - Expecting it to fail as Indeed parsing is disabled
    test_url = "https://www.indeed.com/q-germany-jobs.html?vjk=482f46774f12078f"

    try:
        parser.normalize_url(test_url)
        assert False, "Should have raised Exception because Indeed parsing is disabled"
    except Exception as e:
        assert "Indeed does not allow automatic extracting" in str(e)
        print("✅ Indeed disabled check passed")

    # 2. Test Registry
    registry_parser = ParserRegistry.get_parser(test_url)
    print(f"Registry matched: {type(registry_parser).__name__}")
    assert isinstance(
        registry_parser, IndeedParser
    ), "Registry should return IndeedParser"
    print("✅ Registry OK")


if __name__ == "__main__":
    asyncio.run(test_indeed())
