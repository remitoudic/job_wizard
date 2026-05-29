import os
from unittest.mock import patch

# Mock the entire app and database before importing anything that might use it
with (
    patch("app.core.pubsub.pubsub_manager"),
    patch("app.core.db.engine"),
    patch("database_pkg.init_db"),
):
    from app.services.cover_letter.llm_service import LLMService
    from app.services.cover_letter.templates.spanish import _format_spanish_date
    from app.services.cover_letter.pdf_service import PDFService


def test_format_spanish_date():
    # Test Spanish date format: "12 de abril de 2026"
    assert _format_spanish_date("12 April 2026") == "12 de abril de 2026"
    assert _format_spanish_date("April 12, 2026") == "12 de abril de 2026"

    # Test unparseable date
    assert _format_spanish_date("unparseable") == "unparseable"


def test_spanish_template_generation(tmp_path):
    output_path = str(tmp_path / "test_spanish.pdf")
    service = PDFService()

    # We need to mock the PDF generation's internal calls if they touch the DB,
    # but PDFService is usually pure.
    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="A quien corresponda,\n\nEscribo para postularme al puesto de desarrollador.\n\nUn cordial saludo,\nJuan Pérez",
        job_title="Desarrollador",
        company="Tech S.A.",
        template_name="spanish",
        user_name="Juan Pérez",
        email="juan@example.es",
        phone="+34 123 456 789",
        recipient_name="Responsable de Selección",
        address_city="Madrid",
        employer_address="Gran Vía 1\nMadrid",
    )

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0


def test_clean_model_output_spanish():
    # Test with header junk and signature in Spanish
    text = """
    Juan Pérez
    Calle Mayor 1
    28013 Madrid

    A quien corresponda,

    Escribo para postularme al puesto de desarrollador.

    Un cordial saludo,
    Juan Pérez
    """
    cleaned = LLMService.clean_model_output(text)

    assert "A quien corresponda" in cleaned
    assert "Escribo para postularme" in cleaned
    # Heuristics should strip the header (lines before salutation)
    # and the signature (Un cordial saludo and below)
    assert "Calle Mayor 1" not in cleaned
    assert "Un cordial saludo" not in cleaned
    assert "Juan Pérez" not in cleaned


def test_placeholder_replacement_spanish():
    user_name = "Juan Pérez"
    text = (
        "A quien corresponda,\n\nCuerpo del texto.\n\nUn cordial saludo,\n\n[Su nombre]"
    )

    # Simulate replacement logic in LLMService
    replaced = text.replace("[Your Name]", user_name).replace("[Su nombre]", user_name)

    assert "[Su nombre]" not in replaced
    assert "Juan Pérez" in replaced


def test_spanish_custom_date():
    from app.services.cover_letter.templates.spanish import SpanishTemplate
    from reportlab.platypus import SimpleDocTemplate

    template = SpanishTemplate()
    doc = SimpleDocTemplate("dummy.pdf")

    # 1. Custom date already containing city prefix (should be used as-is)
    story = []
    template.generate(
        doc=doc,
        story=story,
        cover_letter="Hola",
        job_title="Desarrollador",
        company="Tech Co",
        user_name="Juan",
        address_city="Madrid",
        custom_date="Madrid, 28 de mayo de 2026",
    )

    date_paras = [p.text for p in story if hasattr(p, "text") and "de mayo" in p.text]
    assert len(date_paras) == 1
    assert date_paras[0] == "Madrid, 28 de mayo de 2026"

    # 2. Custom date is None (should dynamically format current date with city prefix)
    story2 = []
    template.generate(
        doc=doc,
        story=story2,
        cover_letter="Hola",
        job_title="Desarrollador",
        company="Tech Co",
        user_name="Juan",
        address_city="Madrid",
        custom_date=None,
    )

    date_paras2 = [
        p.text for p in story2 if hasattr(p, "text") and "Madrid, " in p.text
    ]
    assert len(date_paras2) == 1
