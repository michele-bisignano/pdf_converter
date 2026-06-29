import os
import re

# ── Build-time override ─────────────────────────────────────────────────────
# Set this to your Mistral API key before running PyInstaller.
# The key is embedded in the .exe (visible via decompilation — tradeoff accepted).
# In development, the MISTRAL_API_KEY env var takes precedence.
_BUILD_API_KEY: str = ""

# ── Public API ──────────────────────────────────────────────────────────────


def extract_tables_mistral(input_path: str) -> list[str]:
    """
    Sends the PDF to Mistral OCR and returns a list of HTML table strings.

    Uses the Mistral SDK (from mistralai.client import Mistral).
    Tables are extracted from page.markdown via regex since the v2 OCR
    response no longer populates a structured .tables attribute.

    API key resolution: MISTRAL_API_KEY env var > _BUILD_API_KEY > skip.
    """
    api_key = os.environ.get("MISTRAL_API_KEY") or _BUILD_API_KEY
    if not api_key:
        print("\n\tMISTRAL_API_KEY not set -- skipping OCR\n")
        return []

    from mistralai.client import Mistral

    client = Mistral(api_key=api_key)
    uploaded = None

    try:
        with open(input_path, "rb") as f:
            uploaded = client.files.upload(
                file={
                    "file_name": os.path.basename(input_path),
                    "content": f.read(),
                    "content_type": "application/pdf",
                },
                purpose="ocr",
            )

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "file", "file_id": uploaded.id},
            table_format="html",
            extract_header=True,
            extract_footer=True,
            include_image_base64=False,
            confidence_scores_granularity="page",
        )
    except Exception as e:
        print(f"\n\tMistral API error: {e}\n")
        return []
    finally:
        if uploaded is not None:
            try:
                client.files.delete(uploaded.id)
            except Exception:
                pass

    html_tables: list[str] = []
    for page in ocr_response.pages:
        scores = page.confidence_scores
        score = scores.average_page_confidence_score if scores else None
        if score is not None and score < 0.80:
            print(f"\t[warn] page {page.index}: low confidence score ({score:.2f})")
        tables = re.findall(r"<table>.*?</table>", page.markdown, re.DOTALL | re.IGNORECASE)
        html_tables.extend(tables)

    return html_tables
