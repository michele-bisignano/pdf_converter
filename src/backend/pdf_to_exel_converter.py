"""Orchestrator: reads PDF, processes tables, exports to Excel."""
import pandas as pd
from src.backend.extraction.pdf_reader import pdf_reader
from src.backend.extraction.layouts import handle_exceptional_layouts
from src.backend.processing.table_processor import (
    is_table_empty,
    find_row_with_data_and_descrizione,
    copy_table_from_saldo_iniziale,
    get_table_until_saldo_finale,
    headers_delete,
    filter_table_by_header_length,
    filter_table_by_descrizione,
    fix_line_breaks,
    columns_switcher,
)
from src.backend.export.excel_writer import export_to_excel
from src.backend.alternative.processing import validate_saldo
from src.backend.pdf_fallback import pdf_fallback


def pdf_to_excel_converter_main(input_path, output_path):
    """Main function to convert PDF data to an Excel file.

    Attempts deterministic extraction first. Falls back to AI-based
    extraction (Mistral OCR) on failure.

    Args:
        input_path: Path to the input PDF file.
        output_path: Path where the output Excel file will be written.

    Returns:
        Dict with keys: success (bool), warning (bool),
        warning_message (str), validation (dict|None), row_count (int).
    """
    try:
        data = pdf_reader(input_path)

        if is_table_empty(data):
            raise ValueError("Empty table")

        header = find_row_with_data_and_descrizione(data)
        exceptional_table, header = handle_exceptional_layouts(header, input_path)

        if exceptional_table is not None:
            data = exceptional_table

        data = copy_table_from_saldo_iniziale(data)
        data = get_table_until_saldo_finale(data)

        if header:
            data = headers_delete(data, header)
            data = filter_table_by_header_length(data, header)
            data = filter_table_by_descrizione(data, header)
            data = fix_line_breaks(data, header)
            data, header = columns_switcher(data, header)

        export_to_excel(data, header, output_path)

        # Build DataFrame for validation
        df = pd.DataFrame(data, columns=header)
        col_map = {}
        for col in df.columns:
            low = str(col).lower()
            if 'descrizione' in low:
                col_map[col] = 'Descrizione'
            elif 'accredito' in low or 'credito' in low or 'entrate' in low or 'avere' in low:
                col_map[col] = 'Accrediti'
            elif 'addebito' in low or 'debito' in low or 'uscite' in low or 'dare' in low:
                col_map[col] = 'Addebiti'
        df_std = df.rename(columns=col_map)
        for col_name in ['Accrediti', 'Addebiti']:
            if col_name in df_std.columns:
                df_std[col_name] = df_std[col_name].astype(str).str.replace('.', '', regex=False)
                df_std[col_name] = df_std[col_name].str.replace(',', '.', regex=False)
                df_std[col_name] = pd.to_numeric(df_std[col_name], errors='coerce')

        validation = validate_saldo(df_std)

        return {
            "success": True,
            "warning": not validation["valid"],
            "warning_message": validation.get("messaggio", ""),
            "validation": validation,
            "row_count": len(data) - 2,
        }
    except Exception:
        return pdf_fallback(input_path, output_path)
