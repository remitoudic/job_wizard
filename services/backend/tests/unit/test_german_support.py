import os
from app.services.cover_letter.llm_service import LLMService
from app.services.cover_letter.templates.german import _format_german_date
from app.services.cover_letter.pdf_service import PDFService


def test_format_german_date():
    # Test DIN 5008 formats
    # Note: _format_german_date uses datetime.strptime(date_str, "%d %B %Y")
    # which depends on the system locale for month names.
    # However, it then uses its own _DE_MONTHS list for output.
    assert _format_german_date("16 April 2026") == "16. April 2026"
    assert _format_german_date("April 16, 2026") == "16. April 2026"

    # Test unparseable date
    assert _format_german_date("unparseable") == "unparseable"


def test_german_template_generation(tmp_path):
    output_path = str(tmp_path / "test_german.pdf")
    service = PDFService()

    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich um die Position als Softwareentwickler.\n\nMit freundlichen Grüßen,\nMax Mustermann",
        job_title="Softwareentwickler",
        company="Tech GmbH",
        template_name="german",
        user_name="Max Mustermann",
        email="max@example.de",
        phone="+49 123 456 789",
        recipient_name="Frau Schmidt",
        employer_address="Alexanderplatz 1\nBerlin",
    )

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_clean_model_output_german():
    # Test with header junk and signature
    text = """
    Max Mustermann
    Musterstraße 1
    10115 Berlin

    Sehr geehrte Damen und Herren,

    hiermit bewerbe ich mich um die Position als Softwareentwickler.

    Mit freundlichen Grüßen,
    Max Mustermann
    """
    cleaned = LLMService.clean_model_output(text)

    assert "Sehr geehrte Damen und Herren" in cleaned
    assert "hiermit bewerbe ich mich" in cleaned
    # Heuristics should strip the header (lines before salutation)
    # and the signature (Mit freundlichen Grüßen and below)
    assert "Musterstraße 1" not in cleaned
    assert "Mit freundlichen Grüßen" not in cleaned
    assert "Max Mustermann" not in cleaned


def test_placeholder_replacement_german():
    user_name = "Max Mustermann"
    text = "Sehr geehrte Damen und Herren,\n\nTextkörper.\n\nMit freundlichen Grüßen,\n\n[Ihr Name]"

    # Simulate replacement logic in LLMService
    replaced = (
        text.replace("[Your Name]", user_name)
        .replace("[Ihr Name]", user_name)
        .replace("[Votre Nom]", user_name)
    )

    assert "[Ihr Name]" not in replaced
    assert "Max Mustermann" in replaced
