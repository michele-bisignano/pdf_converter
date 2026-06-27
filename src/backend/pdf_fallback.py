"""
Fallback module for AI-based PDF extraction when standard extraction fails.
Delegates to the alternative subpackage.
"""


def pdf_fallback(input_path, output_path):
    """Delegate to alternative's Mistral OCR fallback and return validation.

    Args:
        input_path: Path to the input PDF file.
        output_path: Path where the output Excel file will be written.

    Returns:
        Dict with keys: success (bool), warning (bool),
        warning_message (str), validation (dict|None), row_count (int).
    """
    from src.backend.alternative.main import pdf_fallback as _fallback
    return _fallback(input_path, output_path)
