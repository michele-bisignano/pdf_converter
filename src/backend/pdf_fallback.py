"""
Fallback module for AI-based PDF extraction when standard extraction fails.
Delegates to the alternative subpackage.
"""


def pdf_fallback(input_path, output_path):
    """Delegates to alternative's Mistral OCR fallback."""
    from src.backend.alternative.main import pdf_fallback as _fallback
    _fallback(input_path, output_path)
