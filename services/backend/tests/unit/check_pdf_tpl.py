from app.services.cover_letter.pdf_service import PDFService
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
        template_name="british",
        user_name="John Doe",
        email="john@example.com",
        phone="123-456-7890",
        recipient_name="Jane Smith",
        employer_address="123 High Street\nLondon\nSW1A 1AA",
    )

    if os.path.exists(output_path):
        print(f"Success! PDF created at {output_path}")
        os.remove(output_path)
    else:
        print("Error: PDF not created.")


if __name__ == "__main__":
    test_generation()
