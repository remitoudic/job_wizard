"""
Unit tests to verify PDF margins in cover letter templates.
Ensures top margins are lowered (< 2.5 cm) for a better digital appearance.
"""

import sys
import os

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from reportlab.lib.units import cm, inch

try:
    from app.services.cover_letter.templates.registry import TemplateRegistry
    from app.services.cover_letter.templates.british import BritishTemplate
    from app.services.cover_letter.templates.french import FrenchTemplate
    from app.services.cover_letter.templates.german import GermanTemplate
    from app.services.cover_letter.templates.spanish import SpanishTemplate

    passed = 0
    failed = 0

    def check_margins(template_name, template_class):
        global passed, failed
        print(f"Checking margins for: {template_name}...")
        try:
            instance = template_class()
            margins = instance.get_margins()
            
            # Constraints: Top margin should be <= 2.2 cm (to allow some DIN tolerance but fix the 'too much space' issue)
            # Default BaseTemplate uses 0.75 inch (~1.9 cm)
            top_margin = margins.get('topMargin', 0)
            
            # Print value in cm for readability
            top_cm = top_margin / cm
            print(f"  - Top Margin: {top_cm:.2f} cm")
            
            if top_cm <= 2.2:
                print(f"  ✓ {template_name} top margin OK")
                passed += 1
            else:
                print(f"  ✗ {template_name} top margin TOO LARGE: {top_cm:.2f} cm")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Failed to instantiate or check {template_name}: {e}")
            failed += 1

    # Check all registered templates
    check_margins("German", GermanTemplate)
    check_margins("French", FrenchTemplate)
    check_margins("Spanish", SpanishTemplate)
    check_margins("British", BritishTemplate)

    print(f"\n{'='*50}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    if failed > 0:
        print("MARGIN VERIFICATION FAILED!")
        sys.exit(1)
    else:
        print("ALL MARGIN VERIFICATIONS PASSED")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
