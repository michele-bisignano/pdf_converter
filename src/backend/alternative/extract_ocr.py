import os


def extract_tables_mistral(input_path: str) -> list[str]:
    """
    Sends the PDF to Mistral OCR and returns a list of HTML table strings.
    Uses file upload then references the file_id for OCR processing.

    Requires the MISTRAL_API_KEY environment variable.
    """
    from mistralai.client import Mistral
    from mistralai.client.models import File, FileChunk

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    try:
        with open(input_path, "rb") as f:
            uploaded = client.files.upload(
                file=File(
                    file_name=os.path.basename(input_path),
                    content=f.read(),
                    content_type="application/pdf",
                ),
                purpose="ocr",
            )

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document=FileChunk(file_id=uploaded.id),
            table_format="html",
            extract_header=True,
            extract_footer=True,
            include_image_base64=False,
            confidence_scores_granularity="page",
        )
    except Exception as e:
        print(f"
	Mistral API error: {e}
")
        return []

    html_tables: list[str] = []
    for page in ocr_response.pages:
        scores = page.confidence_scores
        score = scores.average_page_confidence_score if scores else None
        if score is not None and score < 0.80:
            print(f"\t[warn] page {page.index}: low confidence score ({score:.2f})")
        for table in (page.tables or []):
            html_tables.append(table.content)

    return html_tables
