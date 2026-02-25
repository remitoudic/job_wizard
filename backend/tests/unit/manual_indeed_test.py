import asyncio
import logfire
from app.services.job_parsers.job_parser import JobParser

# Configure logfire to print to console only for tests
logfire.configure(send_to_logfire=False)

TEST_URL = "https://de.indeed.com/?vjk=855deef53cd3562f&advn=8743040970454369"

async def test_indeed_parsing():
    print(f"Testing parsing for URL: {TEST_URL}")
    parser = JobParser()
    
    try:
        job_data = await parser.parse_url(TEST_URL)
        if job_data:
            print("\n✅ Parsing Successful!")
            print(f"Title: {job_data.get('title')}")
            print(f"Company: {job_data.get('company')}")
            print(f"Location: {job_data.get('location')}")
            print(f"Description Length: {len(job_data.get('description', ''))} chars")
            print(f"Description Preview: {job_data.get('description', '')[:200]}...")
            print(f"Markdown Content: {bool(job_data.get('markdown_content'))}")
        else:
            print("\n❌ Parsing Failed: No data returned")
            
    except Exception as e:
        print(f"\n❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_indeed_parsing())
