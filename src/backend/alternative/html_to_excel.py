import pandas as pd
from .processing import (
    is_transaction_table,
    parse_html_table,
    select_core_columns,
    extract_riepilogo_simple,
    drop_header_duplicates,
    fix_line_breaks,
    normalize_amounts_df,
    extract_riepilogo_rows,
    df_to_export_format,
)


def html_tables_to_excel(html_tables: list[str], output_path: str) -> None:
    """
    Classify Mistral HTML tables, keep only transaction data,
    clean it, and write a single-sheet Excel file.
    """
    if not html_tables:
        print("\tNessuna tabella estratta dal documento.")
        return

    # ---- Phase 0: extract riepilogo from simple 2-column tables ----
    riepilogo_vals = {}
    for html in html_tables:
        val = extract_riepilogo_simple(html)
        if val:
            riepilogo_vals.update(val)

    if riepilogo_vals:
        print("\tRiepilogo conto:")
        for key, val in riepilogo_vals.items():
            if val is not None:
                print("\t  {}: {:,.2f}".format(key.replace('_', ' ').title(), val))

    # ---- Phase 1: classify and parse transaction tables ----
    all_frames = []
    for html in html_tables:
        if not is_transaction_table(html):
            continue
        df = parse_html_table(html)
        if df is None or df.empty:
            continue
        df = select_core_columns(df)
        if df.empty:
            continue
        all_frames.append(df)

    if not all_frames:
        print("\tNessuna tabella transazioni trovata tra quelle OCR.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    combined = drop_header_duplicates(combined)

    # ---- Phase 2: fix line breaks ----
    combined = fix_line_breaks(combined)

    # ---- Phase 3: discard riepilogo data rows ----
    _, movements = extract_riepilogo_rows(combined)

    # ---- Phase 4: normalize amounts ----
    movements = normalize_amounts_df(movements)

    # ---- Phase 5: final clean-up and export ----
    movements = movements.dropna(subset=['Data Operazione'], how='any').reset_index(drop=True)
    movements = df_to_export_format(movements)

    if movements.empty:
        print("\tNessun movimento valido dopo la pulizia.")
        return

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        movements.to_excel(writer, index=False, sheet_name="Movimenti")
        worksheet = writer.sheets["Movimenti"]
        for col_name in ['Addebiti', 'Accrediti']:
            if col_name not in movements.columns:
                continue
            col_idx = movements.columns.get_loc(col_name)
            col_letter = chr(ord('A') + col_idx)
            for cell in worksheet[col_letter]:
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0.00'

    print("\tSaved {} movimenti -> {}".format(len(movements), output_path))
