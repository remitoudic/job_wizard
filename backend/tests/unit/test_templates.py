import pytest
import os
from app.services.pdf_service import PDFService
from app.services.templates import TemplateRegistry

def test_british_template_generation(tmp_path):
    output_path = str(tmp_path / "test_british.pdf")
    service = PDFService()
    
    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="Dear Hiring Manager,\n\nI am interested in this role.\n\nYours sincerely,\nJohn Doe",
        job_title="Software Engineer",
        company="Tech UK",
        template_name="british",
        user_name="John Doe",
        email="john@example.co.uk",
        phone="+44 123 456 789",
        recipient_name="Jane Smith",
        employer_address="10 Downing Street\nLondon"
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_german_template_generation(tmp_path):
    output_path = str(tmp_path / "test_german.pdf")
    service = PDFService()
    
    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich.\n\nMit freundlichen Grüßen,\nMax Mustermann",
        job_title="Softwareentwickler",
        company="Tech GmbH",
        template_name="german",
        user_name="Max Mustermann",
        email="max@example.de",
        phone="+49 123 456 789",
        recipient_name="Frau Schmidt",
        employer_address="Alexanderplatz 1\nBerlin"
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_template_registry_fallback():
    # Registry should fallback to 'british' if template not found
    template = TemplateRegistry.get("non-existent-template")
    from app.services.templates.british import BritishTemplate
    assert isinstance(template, BritishTemplate)

def test_template_aliases():
    # 'generic' and 'english' should point to BritishTemplate
    from app.services.templates.british import BritishTemplate
    assert isinstance(TemplateRegistry.get("generic"), BritishTemplate)
    assert isinstance(TemplateRegistry.get("english"), BritishTemplate)
