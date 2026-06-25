import pdfplumber


def pdf_reader(pdf_path):
    """
    Reads the PDF and extracts tables.

    Parameters:
    pdf_path (str): The path to the PDF file.

    Returns:
    list of lists: The extracted table data.
    """
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        data.append(row)
    return data
