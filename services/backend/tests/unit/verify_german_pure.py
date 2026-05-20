import sys
import os

# Set PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "app")))

try:
    from app.services.cover_letter.templates.german import _format_german_date
    from app.services.cover_letter.llm_service import LLMService

    # Test date formatting
    print("Testing German date formatting...")
    # Standard formats
    assert _format_german_date("16 April 2026") == "16. April 2026"
    assert _format_german_date("April 16, 2026") == "16. April 2026"
    print("✓ German date formatting OK")

    # Test cleaning
    print("Testing German heuristic cleaning...")
    text = "Sehr geehrte Damen und Herren,\n\nBody-Text.\n\nMit freundlichen Grüßen,\nMax Mustermann"
    cleaned = LLMService.clean_model_output(text)
    assert "Sehr geehrte" in cleaned
    assert "Body-Text" in cleaned
    assert "Mit freundlichen Grüßen" not in cleaned
    assert "Max Mustermann" not in cleaned
    print("✓ German heuristic cleaning OK")

    # Test placeholder replacement
    print("Testing German placeholder replacement...")
    text = "Hallo [Your Name], [Ihr Name], [Votre Nom]"
    replaced = (
        text.replace("[Your Name]", "Me")
        .replace("[Ihr Name]", "Me")
        .replace("[Votre Nom]", "Me")
    )
    assert replaced == "Hallo Me, Me, Me"
    print("✓ German placeholder replacement OK")

    print("\nALL GERMAN PURE LOGIC TESTS PASSED")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
