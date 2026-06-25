from .extract_ocr import extract_tables_mistral
from .html_to_excel import html_tables_to_excel


def pdf_fallback(input_path: str, output_path: str) -> None:
    """
    Fallback extraction via Mistral OCR.
    Called when the primary extractor fails.
    """
    print("\tfallback (Mistral OCR)")
    html_tables = extract_tables_mistral(input_path)
    html_tables_to_excel(html_tables, output_path)
