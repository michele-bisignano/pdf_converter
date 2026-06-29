import os
import pandas as pd
from .processing import (
    is_transaction_table,
    parse_html_table,
    select_core_columns,
    extract_riepilogo_simple,
    drop_header_duplicates,
    fix_line_breaks,
    normalize_amount,
    normalize_amounts_df,
    normalize_saldo_rows,
    validate_saldo,
    df_to_export_format,
    RIEPILOGO_KEYWORDS,
)


def _safe_output_path(original_path: str) -> str:
    """Return a writable path. If original is locked, append _1, _2, etc."""
    if not os.path.exists(original_path):
        return original_path
    try:
        with open(original_path, "a"):
            os.utime(original_path, None)
        return original_path
    except PermissionError:
        base, ext = os.path.splitext(original_path)
        for i in range(1, 100):
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            try:
                with open(candidate, "a"):
                    os.utime(candidate, None)
                return candidate
            except PermissionError:
                continue
        return original_path


def _safe_output_path(original_path: str) -> str:
    """Return a writable path. If original is locked, append _1, _2, etc."""
    if not os.path.exists(original_path):
        return original_path
    try:
        with open(original_path, "a"):
            os.utime(original_path, None)
        return original_path
    except PermissionError:
        base, ext = os.path.splitext(original_path)
        for i in range(1, 100):
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            try:
                with open(candidate, "a"):
                    os.utime(candidate, None)
                return candidate
            except PermissionError:
                continue
        return original_path


def html_tables_to_excel(html_tables: list[str], output_path: str) -> dict:
    """
    Classify Mistral HTML tables, keep only transaction data,
    clean it, and write a single-sheet Excel file.

    Returns a dict with:
      - success: bool
      - warning: bool
      - warning_message: str
      - validation: dict
      - row_count: int
    """
    result = {
        "success": False,
        "warning": False,
        "warning_message": "",
        "validation": None,
        "row_count": 0,
    }

    if not html_tables:
        print("	No tables extracted from the document.")
        return result

    # ---- Phase 0: extract riepilogo from simple 2-column tables ----
    riepilogo_vals = {}
    for html in html_tables:
        val = extract_riepilogo_simple(html)
        if val:
            riepilogo_vals.update(val)

    if riepilogo_vals:
        print("	Account summary:")
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
        print("	No transaction tables found among OCR results.")
        # Fallback: save raw OCR tables so the user can inspect them
        raw_frames = []
        for html in html_tables:
            df = parse_html_table(html)
            if df is not None and not df.empty:
                raw_frames.append(df)

        if raw_frames:
            safe_path = _safe_output_path(output_path)
            with pd.ExcelWriter(safe_path, engine="openpyxl") as writer:
                for i, df in enumerate(raw_frames):
                    sheet_name = f"OCR_Tabella_{i + 1}"[:31]
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
            result["success"] = True
            result["warning"] = True
            result["warning_message"] = (
                "Tabelle OCR salvate senza classificazione: nessuna colonna "
                "transazione riconosciuta. Verificare manualmente il file."
            )
            print(f"	Fallback: saved {len(raw_frames)} raw OCR table(s) -> {safe_path}")
        return result

    combined = pd.concat(all_frames, ignore_index=True)
    combined = drop_header_duplicates(combined)

    # ---- Phase 2: fix line breaks ----
    combined = fix_line_breaks(combined)

    # ---- Phase 3: normalize saldo rows (keep them in the DataFrame) ----
    combined = normalize_saldo_rows(combined)

    # ---- Phase 4: normalize amounts ----
    combined = normalize_amounts_df(combined)

    # ---- Phase 5: final clean-up ----
    combined = combined.dropna(subset=['Data Operazione'], how='any').reset_index(drop=True)
    export_df = df_to_export_format(combined)

    if export_df.empty:
        print("	No valid transactions after cleaning.")
        return result

    # ---- Phase 6: validation ----
    validation = validate_saldo(export_df, riepilogo_vals)
    result["validation"] = validation

    if not validation["valid"]:
        result["warning"] = True
        result["warning_message"] = validation["messaggio"]
        print("\n\t" + validation["messaggio"])

    # ---- Phase 7: write to Excel ----
    output_path = _safe_output_path(output_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Movimenti")
        worksheet = writer.sheets["Movimenti"]
        for col_name in ['Addebiti', 'Accrediti']:
            if col_name not in export_df.columns:
                continue
            col_idx = export_df.columns.get_loc(col_name)
            col_letter = chr(ord('A') + col_idx)
            for cell in worksheet[col_letter]:
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0.00'

    # Count only transaction rows (exclude saldo/riepilogo rows)
    if 'Descrizione' in export_df.columns:
        riepilogo_mask = pd.Series(False, index=export_df.index)
        for kw in RIEPILOGO_KEYWORDS:
            riepilogo_mask |= export_df['Descrizione'].astype(str).str.lower().str.contains(kw, na=False)
        row_count = len(export_df[~riepilogo_mask])
    else:
        row_count = len(export_df)
    print("	Saved {} transactions -> {}".format(row_count, output_path))
    result["success"] = True
    result["row_count"] = row_count
    return result
