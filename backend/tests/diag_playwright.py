try:
    from playwright.async_api import async_playwright
    print("SUCCESS: playwright.async_api imported")
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
except Exception as e:
    print(f"OTHER_ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
