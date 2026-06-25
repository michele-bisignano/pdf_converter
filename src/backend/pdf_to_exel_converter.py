# Orchestrator: reads PDF, processes tables, exports to Excel.
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
from src.backend.pdf_fallback import pdf_fallback


def pdf_to_excel_converter_main(input_path, output_path):
    """Main function to convert PDF data to an Excel file."""
    try:
        data = pdf_reader(input_path)

        if is_table_empty(data):
            raise ValueError("Tabella vuota")

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
    except Exception:
        pdf_fallback(input_path, output_path)
