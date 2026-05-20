from pathlib import Path

import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Service for parsing text from PDF files"""

    def extract_text(self, file_path: str | Path) -> str:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            str: Extracted text content
        """
        try:
            import edgeparse

            text = edgeparse.convert(str(file_path), format="markdown")
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
