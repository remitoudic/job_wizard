import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the app directory to the path so imports work
sys.path.append("/app")

from app.services.cv_parser_service import cv_parser_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_parser")

async def main():
    pdf_path = "/app/tests/test_cv/Rémi_Toudic_CV_26 .pdf"
    
    if not Path(pdf_path).exists():
        logger.error(f"Cannot find PDF at {pdf_path}")
        return

    logger.info(f"Parsing {pdf_path}...")
    
    try:
        cv_data = await cv_parser_service.parse_pdf(pdf_path)
        logger.info("Extraction successful!")
        
        # Dump just the experiences to see what we got
        experiences = cv_data.model_dump().get("experiences", [])
        
        print("\n" + "="*50)
        print(f"Extracted {len(experiences)} experiences:")
        print("="*50)
        
        print(json.dumps(experiences, indent=2))
        
        print("\n" + "="*50)
        print("Extracted contact info:")
        print("="*50)
        print(cv_data.contact.model_dump_json(indent=2))
        
        print("\n" + "="*50)
        print("Summary extracted:")
        print("="*50)
        print(cv_data.summary[:500] + "..." if cv_data.summary else "None")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
