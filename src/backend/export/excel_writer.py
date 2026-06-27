import pandas as pd


def export_to_excel(data, header, output_path):
    """Write data to Excel file."""
    if header:
        df = pd.DataFrame(data, columns=header)
    else:
        from src.backend.utils.table_utils import max_row_length
        df = pd.DataFrame(data, columns=max_row_length(data))

    df.to_excel(output_path, index=False)
    print(f"Excel file saved to: {output_path}")
