from .extract_ocr import extract_tables_mistral
from .html_to_excel import html_tables_to_excel


def pdf_fallback(input_path: str, output_path: str) -> dict:
    """
    Fallback extraction via Mistral OCR.
    Called when the primary extractor fails.
    Returns a dict with success/warning/validation info.
    """
    print("\tfallback (Mistral OCR)")
    html_tables = extract_tables_mistral(input_path)
    return html_tables_to_excel(html_tables, output_path)
