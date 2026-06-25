import pandas as pd


def html_tables_to_excel(html_tables: list[str], output_path: str) -> None:
    """
    Parses a list of HTML table strings and writes all rows to a single
    Excel sheet, concatenated in order (one table after the other).
    """
    if not html_tables:
        raise ValueError("Mistral OCR: no tables found in the document.")

    all_dfs: list[pd.DataFrame] = []
    for html in html_tables:
        try:
            dfs = pd.read_html(html, flavor="lxml")
            all_dfs.extend(dfs)
        except Exception as e:
            print(f"\t[warn] Could not parse table: {e}")

    if not all_dfs:
        raise ValueError("Mistral OCR: failed to parse any table from HTML.")

    combined = pd.concat(all_dfs, ignore_index=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        combined.to_excel(writer, index=False, sheet_name="Sheet1")

    print(f"\tSaved {len(all_dfs)} table(s) → {output_path}")
