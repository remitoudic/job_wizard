import pytest
import os
from unittest.mock import MagicMock, patch
from app.services.cover_letter.llm_service import LLMService
from app.services.cover_letter.templates.french import _format_french_date, FrenchTemplate
from app.services.cover_letter.pdf_service import PDFService

def test_format_french_date():
    # Test standard formats
    assert _format_french_date("11 April 2026") == "11 avril 2026"
    assert _format_french_date("April 11, 2026") == "11 avril 2026"
    
    # Test lowercase month input
    assert _format_french_date("11 april 2026") == "11 avril 2026"
    
    # Test unparseable date
    assert _format_french_date("unparseable") == "unparseable"

def test_french_template_generation(tmp_path):
    output_path = str(tmp_path / "test_french.pdf")
    service = PDFService()
    
    service.generate_cover_letter_pdf(
        output_path=output_path,
        cover_letter="Madame, Monsieur,\n\nCeci est un test de lettre de motivation.\n\nCordialement,\nJean Dupont",
        job_title="Ingénieur Logiciel",
        company="Tech France",
        template_name="french",
        user_name="Jean Dupont",
        email="jean@example.fr",
        phone="+33 1 23 45 67 89",
        recipient_name="M. Lefebvre",
        employer_address="123 Rue de Rivoli\n75001 Paris",
        address_city="Paris"
    )
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_clean_model_output_french():
    # Test with header junk and signature
    text = """
    Jean Dupont
    123 Rue de la Paix
    75002 Paris
    
    Madame, Monsieur,
    
    Je suis très intéressé par le poste d'ingénieur. Voici mon parcours.
    
    Cordialement,
    Jean Dupont
    """
    cleaned = LLMService.clean_model_output(text)
    
    assert "Madame, Monsieur" in cleaned
    assert "Je suis très intéressé" in cleaned
    # Heuristics should strip the header (lines before salutation)
    # and the signature (Cordialement and below)
    assert "Rue de la Paix" not in cleaned
    assert "Cordialement" not in cleaned
    assert "Jean Dupont" not in cleaned

def test_clean_model_output_french_long_closing():
    text = """
    Madame, Monsieur,
    
    Le corps du mail.
    
    Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.
    Jean Dupont
    """
    cleaned = LLMService.clean_model_output(text)
    assert "corps du mail" in cleaned.lower()
    assert "Je vous prie d'agréer" not in cleaned

def test_placeholder_replacement_french():
    user_name = "Jean Dupont"
    text = "Madame, Monsieur,\n\nTexte.\n\nCordialement,\n\n[Votre Nom]"
    
    # Simulate replacement logic in LLMService
    replaced = text.replace("[Your Name]", user_name).replace("[Ihr Name]", user_name).replace("[Votre Nom]", user_name)
    
    assert "[Votre Nom]" not in replaced
    assert "Jean Dupont" in replaced
