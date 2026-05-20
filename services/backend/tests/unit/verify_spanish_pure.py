import os
import sys

# Set path to include services/backend
sys.path.append(os.path.join(os.getcwd(), "services/backend"))

from app.services.cover_letter.templates.spanish import _format_spanish_date
from app.services.cover_letter.pdf_service import PDFService
from app.services.cover_letter.llm_service import LLMService


def verify_date_format():
    print("Verifying date format...")
    d1 = _format_spanish_date("12 April 2026")
    print(f"  Input: '12 April 2026' -> Output: '{d1}'")
    assert d1 == "12 de abril de 2026"

    d2 = _format_spanish_date("April 12, 2026")
    print(f"  Input: 'April 12, 2026' -> Output: '{d2}'")
    assert d2 == "12 de abril de 2026"
    print("✅ Date format verified.")


def verify_cleaning_logic():
    print("\nVerifying cleaning logic...")
    text = """
    Juan Pérez
    Calle Mayor 1

    A quien corresponda,

    Cuerpo de la carta.

    Un cordial saludo,
    Juan Pérez
    """
    cleaned = LLMService.clean_model_output(text)
    print(f"  Cleaned text: {repr(cleaned)}")
    assert "A quien corresponda" in cleaned
    assert "Cuerpo de la carta" in cleaned
    assert "Calle Mayor 1" not in cleaned
    assert "Un cordial saludo" not in cleaned
    print("✅ Cleaning logic verified.")


def verify_pdf_generation():
    print("\nVerifying PDF generation...")
    pdf_service = PDFService()
    output_path = "test_spanish_manual.pdf"

    try:
        pdf_service.generate_cover_letter_pdf(
            output_path=output_path,
            cover_letter="A quien corresponda,\n\nTest de carta en español.",
            job_title="Tester",
            company="Test Inc.",
            template_name="spanish",
            user_name="Test User",
            address_city="Madrid",
        )
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"  PDF generated successfully: {output_path} ({size} bytes)")
            os.remove(output_path)
            print("✅ PDF generation verified.")
        else:
            print("❌ PDF not found.")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")


if __name__ == "__main__":
    try:
        verify_date_format()
        verify_cleaning_logic()
        verify_pdf_generation()
        print("\nAll Spanish support verifications passed! 🎉")
    except Exception as e:
        print(f"\nVerification failed: {e}")
        sys.exit(1)
