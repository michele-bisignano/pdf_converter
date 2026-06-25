import os
import base64


def extract_tables_mistral(input_path: str) -> list[str]:
    """
    Sends the PDF to Mistral OCR and returns a list of HTML table strings,
    one entry per table found across all pages.

    Requires the MISTRAL_API_KEY environment variable.
    """
    from mistralai import Mistral

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    with open(input_path, "rb") as f:
        pdf_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_base64",
            "document_base64": pdf_b64,
        },
        table_format="html",        # tables as separate HTML objects → pd.read_html()
        extract_header=True,
        extract_footer=True,
        include_image_base64=False,
        confidence_scores_granularity="page",
    )

    html_tables: list[str] = []
    for page in ocr_response.pages:
        score = (page.confidence_scores or {}).get("average_page_confidence_score")
        if score is not None and score < 0.80:
            print(f"\t[warn] page {page.index}: low confidence score ({score:.2f})")
        for table in (page.tables or []):
            html_tables.append(table.content)

    return html_tables
