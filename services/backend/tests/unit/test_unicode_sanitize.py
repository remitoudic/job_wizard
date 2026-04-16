"""
Unit tests for Unicode sanitization in PDF generation.

ReportLab's built-in fonts (Helvetica, Times-Roman) only support Latin-1.
LLMs frequently emit special Unicode characters (smart hyphens, curly quotes,
zero-width spaces) that render as black boxes (■) in the PDF output.

BaseTemplate.sanitize_text() normalises these to safe equivalents.
These tests ensure the sanitizer catches all known problem characters
without destroying valid Latin-1 content (umlauts, accents, etc.).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from app.services.cover_letter.templates.base import BaseTemplate

    sanitize = BaseTemplate.sanitize_text
    passed = 0
    failed = 0

    def check(label, input_text, expected):
        global passed, failed
        result = sanitize(input_text)
        if result == expected:
            print(f"  ✓ {label}")
            passed += 1
        else:
            print(f"  ✗ {label}")
            print(f"    Input:    {repr(input_text)}")
            print(f"    Expected: {repr(expected)}")
            print(f"    Got:      {repr(result)}")
            failed += 1

    # ── Hyphens & Dashes ──────────────────────────────────────────────
    print("Testing hyphens & dashes...")
    check("U+2010 HYPHEN",              "Backend\u2010Systeme",         "Backend-Systeme")
    check("U+2011 NON-BREAKING HYPHEN", "Release\u2011Zeit",           "Release-Zeit")
    check("U+2012 FIGURE DASH",         "Test\u2012Wert",              "Test-Wert")
    check("U+2013 EN DASH",             "Performance\u2013Steigerung", "Performance-Steigerung")
    check("U+2014 EM DASH",             "Server\u2014Kosten",          "Server-Kosten")
    check("U+2015 HORIZONTAL BAR",      "A\u2015B",                    "A-B")
    check("U+00AD SOFT HYPHEN removed", "Caching\u00ADStrategien",     "CachingStrategien")
    check("U+FE63 SMALL HYPHEN-MINUS",  "X\uFE63Y",                   "X-Y")
    check("U+FF0D FULLWIDTH HYPHEN",    "A\uFF0DB",                    "A-B")
    check("ASCII hyphen unchanged",     "already-hyphenated",          "already-hyphenated")

    # ── Quotation Marks ───────────────────────────────────────────────
    print("Testing quotation marks...")
    check("Smart double quotes",  "\u201CHello\u201D",      '"Hello"')
    check("Smart single quotes",  "\u2018it\u2019s\u2019",  "'it's'")
    check("Low-9 double quote",   "\u201EText\u201C",       '"Text"')
    check("Guillemets",           "\u00ABBonjour\u00BB",     '"Bonjour"')
    check("ASCII quotes unchanged", '"normal" \'quotes\'',  '"normal" \'quotes\'')

    # ── Zero-Width & Invisible Characters ─────────────────────────────
    print("Testing zero-width & invisible characters...")
    check("U+200B ZERO WIDTH SPACE",    "Workforce\u200BManagement",  "WorkforceManagement")
    check("U+200C ZERO WIDTH NON-JOINER", "A\u200CB",                 "AB")
    check("U+200D ZERO WIDTH JOINER",     "A\u200DB",                 "AB")
    check("U+FEFF BOM",                   "\uFEFFText",               "Text")
    check("U+00A0 NON-BREAKING SPACE",    "word\u00A0word",           "word word")
    check("U+2003 EM SPACE",              "A\u2003B",                 "A B")
    check("U+202F NARROW NO-BREAK SPACE", "100\u202F000",             "100 000")

    # ── Dots & Bullets ────────────────────────────────────────────────
    print("Testing dots & bullets...")
    check("U+2026 HORIZONTAL ELLIPSIS", "Wait\u2026",    "Wait...")
    check("U+2022 BULLET",             "\u2022 Item",    "- Item")

    # ── German Characters (MUST be preserved) ─────────────────────────
    print("Testing German character preservation...")
    check("ü preserved", "Grüße",   "Grüße")
    check("ö preserved", "können",  "können")
    check("ä preserved", "Händler", "Händler")
    check("ß preserved", "Straße",  "Straße")
    check("Ü preserved", "Übung",   "Übung")
    check("Ö preserved", "Österreich", "Österreich")
    check("Ä preserved", "Änderung",   "Änderung")

    # ── French Characters (MUST be preserved) ─────────────────────────
    print("Testing French character preservation...")
    check("é preserved", "résumé",      "résumé")
    check("è preserved", "très",        "très")
    check("ê preserved", "être",        "être")
    check("ç preserved", "français",    "français")
    check("à preserved", "à bientôt",   "à bientôt")
    check("ù preserved", "où",          "où")

    # ── Spanish Characters (MUST be preserved) ────────────────────────
    print("Testing Spanish character preservation...")
    check("ñ preserved",  "España",     "España")
    check("¿ preserved",  "¿Qué tal?",  "¿Qué tal?")
    check("¡ preserved",  "¡Hola!",     "¡Hola!")

    # ── Edge Cases ────────────────────────────────────────────────────
    print("Testing edge cases...")
    check("Empty string",    "",    "")
    check("None returns None", None, None)
    check("Pure ASCII",      "Hello World 123!", "Hello World 123!")
    check("Multiple replacements in one string",
          "Backend\u2010Systeme und Datenverarbeitungs\u2013Workflows mit \u201CSmart\u201D Quotes",
          'Backend-Systeme und Datenverarbeitungs-Workflows mit "Smart" Quotes')

    # ── Realistic LLM Output (Integration-style) ─────────────────────
    print("Testing realistic LLM German output...")
    llm_output = (
        "Sehr geehrte Damen und Herren,\n\n"
        "mit gro\u00dfer Motivation bewerbe ich mich als Senior Python Backend Engineer "
        "bei eRecht24 IT GmbH. Durch mehrj\u00e4hrige Erfahrung in der Entwicklung "
        "skalierbarer Backend\u2011Systeme mit Python, Django und FastAPI sowie "
        "nachweisliche Erfolge in der Optimierung von "
        "Datenverarbeitungs\u2010Workflows, bin ich \u00fcberzeugt, Ihre Plattform "
        "technisch weiter zu st\u00e4rken.\n\n"
        "In meiner letzten Position habe ich ein komplettes "
        "Workforce\u200BManagement\u200BSystem von Grund auf konzipiert."
    )
    sanitized = sanitize(llm_output)
    assert "Backend-Systeme" in sanitized, "Unicode hyphen not replaced in LLM output"
    assert "Datenverarbeitungs-Workflows" in sanitized, "Unicode hyphen not replaced"
    assert "WorkforceManagementSystem" in sanitized, "Zero-width space not removed"
    assert "großer" in sanitized, "German ß lost"
    assert "überzeugt" in sanitized, "German ü lost"
    assert "stärken" in sanitized, "German ä lost"
    assert "\u2011" not in sanitized, "NON-BREAKING HYPHEN still present"
    assert "\u2010" not in sanitized, "HYPHEN still present"
    assert "\u200B" not in sanitized, "ZERO WIDTH SPACE still present"
    print("  ✓ Realistic German LLM output sanitized correctly")
    passed += 1

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    if failed > 0:
        print("SOME TESTS FAILED!")
        sys.exit(1)
    else:
        print("ALL UNICODE SANITIZATION TESTS PASSED")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
