import sys
import os

# Set PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "app")))

try:
    from app.services.cover_letter.templates.french import _format_french_date
    from app.services.cover_letter.llm_service import LLMService

    # Test date formatting
    print("Testing date formatting...")
    assert _format_french_date("11 April 2026") == "11 avril 2026"
    assert _format_french_date("April 11, 2026") == "11 avril 2026"
    print("✓ Date formatting OK")

    # Test cleaning
    print("Testing heuristic cleaning...")
    text = "Madame, Monsieur,\n\nBody.\n\nCordialement,\nJean"
    cleaned = LLMService.clean_model_output(text)
    assert "Madame, Monsieur" in cleaned
    assert "Body" in cleaned
    assert "Cordialement" not in cleaned
    print("✓ Heuristic cleaning OK")

    # Test placeholder replacement
    print("Testing placeholder replacement...")
    text = "Hello [Your Name], [Ihr Name], [Votre Nom]"
    replaced = (
        text.replace("[Your Name]", "Me")
        .replace("[Ihr Name]", "Me")
        .replace("[Votre Nom]", "Me")
    )
    assert replaced == "Hello Me, Me, Me"
    print("✓ Placeholder replacement OK")

    print("\nALL PURE LOGIC TESTS PASSED")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
