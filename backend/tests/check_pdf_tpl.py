from app.services.pdf_service import PDFService
import os

def test_generation():
    service = PDFService()
    output_path = "test_output.pdf"
    
    print("Generating PDF with 'generic' template...")
    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="This is a test cover letter.\n\nIt has multiple paragraphs.",
        job_title="Software Engineer",
        company="Tech Corp",
        template_name="generic",
        user_name="John Doe",
        email="john@example.com",
        phone="123-456-7890"
    )
    
    if os.path.exists(output_path):
        print(f"Success! PDF created at {output_path}")
        os.remove(output_path)
    else:
        print("Error: PDF not created.")

if __name__ == "__main__":
    test_generation()
