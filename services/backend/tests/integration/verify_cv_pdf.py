import asyncio
from app.services.cv_refresh.cv_parsers.cv_parser_service import cv_parser_service
from app.services.cv_refresh.cv_generator_service import cv_generator_service


async def main():
    print("Parsing long CV...")
    cv_data = await cv_parser_service.parse_pdf(
        "/app/tests/integration/test_cv/Rémi_Toudic_CV_26 .pdf"
    )
    print(f"Parsed {len(cv_data.experiences)} experiences.")

    print("Generating modern (2-col) PDF...")
    cv_generator_service.generate_pdf(
        cv_data, "modern", "/app/tests/integration/test_cv_modern_floats.pdf"
    )

    print("Generating modern (1-col) PDF...")
    cv_generator_service.generate_pdf(
        cv_data, "modern_single", "/app/tests/integration/test_cv_modern_single.pdf"
    )

    print("Generating classic PDF...")
    cv_generator_service.generate_pdf(
        cv_data, "classic", "/app/tests/integration/test_cv_classic.pdf"
    )
    print("Done! PDFs saved to /app/tests/integration")


if __name__ == "__main__":
    asyncio.run(main())
