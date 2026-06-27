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
    extract_riepilogo_rows,
    df_to_export_format,
)


def validate_saldo(saldo_iniziale: float | None, movements: pd.DataFrame, saldo_finale: float | None) -> dict:
    """
    Validate: saldo_iniziale + total_credits - total_debits ≈ saldo_finale.
    Returns a dict with result and details.
    """
    total_accrediti = movements['Accrediti'].sum() if 'Accrediti' in movements and not movements['Accrediti'].empty else 0
    total_addebiti = movements['Addebiti'].sum() if 'Addebiti' in movements and not movements['Addebiti'].empty else 0

    if pd.isna(total_accrediti):
        total_accrediti = 0
    if pd.isna(total_addebiti):
        total_addebiti = 0

    result = {
        "saldo_iniziale": round(saldo_iniziale, 2) if saldo_iniziale is not None else None,
        "totale_accrediti": round(total_accrediti, 2),
        "totale_addebiti": round(total_addebiti, 2),
        "saldo_finale_dichiarato": round(saldo_finale, 2) if saldo_finale is not None else None,
        "saldo_calcolato": None,
        "differenza": None,
        "valid": True,
        "messaggio": "",
    }

    if saldo_iniziale is not None and saldo_finale is not None:
        saldo_calcolato = saldo_iniziale + total_accrediti - total_addebiti
        result["saldo_calcolato"] = round(saldo_calcolato, 2)
        diff = round(abs(saldo_calcolato - saldo_finale), 2)
        result["differenza"] = diff

        if diff > 0.01:
            result["valid"] = False
            result["messaggio"] = (
                f"Warning: the calculated balance ({saldo_calcolato:,.2f}) "
                f"does not match the declared final balance ({saldo_finale:,.2f}). "
                f"Difference: {diff:,.2f}."
            )

    return result


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
        return result

    combined = pd.concat(all_frames, ignore_index=True)
    combined = drop_header_duplicates(combined)

    # ---- Phase 2: fix line breaks ----
    combined = fix_line_breaks(combined)

    # ---- Phase 3: split riepilogo data rows ----
    riepilogo, movements = extract_riepilogo_rows(combined)

    # ---- Phase 4: normalize amounts ----
    movements = normalize_amounts_df(movements)

    # ---- Phase 5: final clean-up ----
    movements = movements.dropna(subset=['Data Operazione'], how='any').reset_index(drop=True)
    movements = df_to_export_format(movements)

    if movements.empty:
        print("	No valid transactions after cleaning.")
        return result

    # ---- Phase 6: validation (BEFORE adding riepilogo rows) ----
    saldo_iniziale_val = riepilogo_vals.get('saldo_iniziale')
    saldo_finale_val = riepilogo_vals.get('saldo_finale')

    # Also look for initial/final balance in transaction summary rows
    if saldo_iniziale_val is None and not riepilogo.empty:
        for _, r in riepilogo.iterrows():
            desc = str(r.get('Descrizione', '')).lower() if pd.notna(r.get('Descrizione')) else ''
            if 'saldo iniziale' in desc or 'saldo precedente' in desc:
                amount_a = r.get('Accrediti') if 'Accrediti' in r else None
                amount_d = r.get('Addebiti') if 'Addebiti' in r else None
                saldo_iniziale_val = normalize_amount(amount_a) if pd.notna(amount_a) else normalize_amount(amount_d)
            if 'saldo finale' in desc or 'saldo del periodo' in desc:
                amount_a = r.get('Accrediti') if 'Accrediti' in r else None
                amount_d = r.get('Addebiti') if 'Addebiti' in r else None
                saldo_finale_val = normalize_amount(amount_a) if pd.notna(amount_a) else normalize_amount(amount_d)

    validation = validate_saldo(saldo_iniziale_val, movements, saldo_finale_val)
    result["validation"] = validation

    if not validation["valid"]:
        result["warning"] = True
        result["warning_message"] = validation["messaggio"]
        print("\n\t" + validation["messaggio"])

    # ---- Phase 7: add riepilogo rows (saldo iniziale / saldo finale) to export ----
    export_df = movements.copy()
    if saldo_iniziale_val is not None:
        saldo_row = {col: None for col in export_df.columns}
        saldo_row['Descrizione'] = 'SALDO INIZIALE'
        if saldo_iniziale_val >= 0:
            saldo_row['Accrediti'] = round(saldo_iniziale_val, 2)
        else:
            saldo_row['Addebiti'] = round(abs(saldo_iniziale_val), 2)
        saldo_row_df = pd.DataFrame([saldo_row]).astype(export_df.dtypes.to_dict())
        export_df = pd.concat([saldo_row_df, export_df], ignore_index=True)

    if saldo_finale_val is not None:
        saldo_row = {col: None for col in export_df.columns}
        saldo_row['Descrizione'] = 'SALDO FINALE'
        if saldo_finale_val >= 0:
            saldo_row['Accrediti'] = round(saldo_finale_val, 2)
        else:
            saldo_row['Addebiti'] = round(abs(saldo_finale_val), 2)
        saldo_row_df = pd.DataFrame([saldo_row]).astype(export_df.dtypes.to_dict())
        export_df = pd.concat([export_df, saldo_row_df], ignore_index=True)

    # ---- Phase 8: write to Excel ----
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

    row_count = len(movements)
    print("	Saved {} transactions -> {}".format(row_count, output_path))
    result["success"] = True
    result["row_count"] = row_count
    return result
