import os
import sys

# Add backend to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.services.cv_refresh.cv_generator_service import cv_generator_service
from app.services.cv_refresh.cv_parsers.cv_parser_service import CVData

sample_data = CVData(
    contact={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "123-456-7890",
        "linkedin": "linkedin.com/in/janedoe",
        "address": "New York, NY",
    },
    summary="A highly skilled software engineer with 5 years of experience building scalable web applications.",
    experiences=[
        {
            "title": "Senior Engineer",
            "company": "Tech Corp",
            "start_date": "Jan 2020",
            "end_date": "Present",
            "description": "Led the backend team.\nImproved performance by 50%.",
        }
    ],
    education=[
        {
            "degree": "B.S. Computer Science",
            "institution": "University of Tech",
            "start_date": "2015",
            "end_date": "2019",
        }
    ],
    skills=["Python", "Svelte", "PostgreSQL"],
    languages=["English", "Spanish"],
)

if __name__ == "__main__":
    try:
        # Generate the PDF
        pdf_bytes = cv_generator_service.generate_pdf(
            cv_data=sample_data,
            template_name="time_line",
            output_path="/tmp/test_timeline_cv.pdf",
        )
        print("Successfully generated /tmp/test_timeline_cv.pdf")
    except Exception as e:
        print(f"Error: {e}")
