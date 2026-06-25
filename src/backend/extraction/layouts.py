# This file contains functions to handle Credem and Credit_Agricole pdf
import io
import fitz  # PyMuPDF
import re
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from src.backend.extraction.pdf_reader import pdf_reader
from src.backend.utils.table_utils import column_writer
from src.backend.io.file_manager import generate_column_file_path, delete_pdf

def handle_exceptional_layouts(header, input_path):
    """
    Check if the table belongs to Credem or Credit Agricole bank and process accordingly.
    If the table does not belong to either bank, the function returns None.
    """

    # Define the expected headers for Credem and Crédit Agricole banks
    credem_header = [None, 'DATA VALUTA', 'DESCRIZIONE OPERAZIONE', 'IMPORTO A DEBITO', None]
    credit_agricole_header = [
        "Data", 
        "Valuta", 
        "Movimenti dare", 
        "Movimenti avere", 
        "Descrizione operazioni", 
        "Riferimenti"
    ]

    # Generate the file path for the PDF that contains columns
    pdf_path_with_columns = generate_column_file_path()

    # Initialize table as None
    table = None

    # Check if the header matches the Credem header
    if header == credem_header:
        # Adjust the header to the expected format for Credem processing
        header = [
            "DATA CONTABILE", 
            "DATA VALUTA", 
            "DESCRIZIONE OPERAZIONE", 
            "IMPORTO A DEBITO", 
            "IMPORTO A CREDITO"
        ]
        # Handle the Credem file using the adjusted header
        handle_credem_file(header, input_path)
        
        # Read the processed PDF file with columns into a table
        table = pdf_reader(pdf_path_with_columns)

        # Extract the data and dates from the left column
        all_table = extract_left_column_data(pdf_path_with_columns)
        left_column_data = extract_dates_from_left_column(all_table)
        
        # Write the dates back to the table
        table = column_writer(table, 0, left_column_data, 2)  # The value 2 is due to the presence of the header and the initial balance

    # Check if the header matches the Crédit Agricole header
    elif header == credit_agricole_header:
        # Handle the Crédit Agricole file
        handle_credit_agricole(header, input_path)

        # Read the processed PDF file with columns into a table
        table = pdf_reader(pdf_path_with_columns)

    # Delete the temporary PDF file generated earlier
    delete_pdf(pdf_path_with_columns)

    # Return the final table data and the modified header
    return table, header

def draw_columns(x_coords, y_top, y_bottom, canvas_obj, line_widths, default_line_width=1):
    """
    Draws vertical lines on the canvas for each x in x_coords. The lines extend from y_top to y_bottom.

    Parameters:
    x_coords (list): List of x-coordinates where the lines will be drawn.
    y_top (float): The top y-coordinate where the lines start.
    y_bottom (float): The bottom y-coordinate where the lines end.
    canvas_obj (Canvas): The canvas object where lines will be drawn.
    line_widths (list): List of line widths for each line.
    default_line_width (int, optional): Default line width if line_widths is shorter than x_coords. Defaults to 1.
    """
    # Calculate the difference in lengths between x_coords and line_widths
    diff = len(x_coords) - len(line_widths)

    for i, x in enumerate(x_coords):
        # Determine the line width to use
        if i < diff:
            lw = default_line_width
        else:
            lw = line_widths[i - diff]
        
        # Set the line width and draw the line
        canvas_obj.setLineWidth(lw)
        canvas_obj.line(x, y_top, x, y_bottom)

def get_header_top_y(header_rects):
    """
    Returns the highest y-coordinate among the header rectangles.

    Parameters:
    header_rects (dict): A dictionary containing header names as keys and their corresponding rectangles as values.

    Returns:
    float: The highest y-coordinate (minimum y0 value) among the header rectangles.
    """
    return min(rect.y0 for rect in header_rects.values())

def get_header_rects(page, headers):
    """
    Finds the rectangles for the given headers on a page.

    Parameters:
    page (Page): The page object to search for headers.
    headers (list): A list of header names to search for.

    Returns:
    dict: A dictionary containing header names as keys and their corresponding rectangles as values.
    """
    header_rects = {}
    for header in headers:
        rects = page.search_for(header)
        if rects:
            header_rects[header] = rects[0]
    return header_rects

def draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl, line_widths):
    """
    Creates an overlay with ReportLab to draw the columns.

    Parameters:
    page_width (float): The width of the page.
    page_height (float): The height of the page.
    x_coords (list): List of x-coordinates where the lines will be drawn.
    y_top_rl (float): The top y-coordinate in ReportLab's coordinate system.
    y_bottom_rl (float): The bottom y-coordinate in ReportLab's coordinate system.
    line_widths (list): List of line widths for each line.

    Returns:
    BytesIO: A BytesIO object containing the overlay PDF.
    """
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    c.setStrokeColorRGB(0, 0, 0)  # Set the line color (black)
    draw_columns(x_coords, y_top_rl, y_bottom_rl, c, line_widths)
    c.save()
    packet.seek(0)
    return packet

def merge_overlay(reader, writer, overlay_packet, page_index):
    """
    Merges the overlay with the original page using PyPDF2.

    Parameters:
    reader (PdfReader): The PdfReader object for the original PDF.
    writer (PdfWriter): The PdfWriter object for the output PDF.
    overlay_packet (BytesIO): A BytesIO object containing the overlay PDF.
    page_index (int): The index of the page to merge the overlay with.
    """
    overlay_pdf = PdfReader(overlay_packet)
    overlay_page = overlay_pdf.pages[0]
    
    page_to_merge = reader.pages[page_index]
    page_to_merge.merge_page(overlay_page)
    writer.add_page(page_to_merge)


def convert_to_reportlab_coords(header_top_y, table_bottom_y, page_height):
    """
    Converts coordinates from MuPDF to ReportLab (bottom left origin).

    Parameters:
    header_top_y (float): The top y-coordinate of the header in MuPDF coordinates.
    table_bottom_y (float): The bottom y-coordinate of the table in MuPDF coordinates.
    page_height (float): The height of the page.

    Returns:
    tuple: The converted y-coordinates for ReportLab.
    """
    y_top_rl = page_height - header_top_y
    y_bottom_rl = page_height - table_bottom_y
    return y_top_rl, y_bottom_rl

def draw_column_lines_on_pdf(headers, x_coords, table_bottom_y, input_pdf, line_widths):
    """
    Main function that draws columns on each page of the PDF.

    Parameters:
    headers (list): List of header names to search for.
    x_coords (list): List of x-coordinates where the lines will be drawn.
    table_bottom_y (float): The bottom y-coordinate of the table.
    input_pdf (str): Path to the input PDF file.
    line_widths (list): List of line widths for each line.
    """
    doc = fitz.open(input_pdf)
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Find the first occurrence of "final balance" (or "saldo fine") starting from the last page
    saldo_finale_info = find_saldo_finale(doc)

    # Determine the last page to process:
    if saldo_finale_info is not None:
        stop_page = saldo_finale_info[0]
    else:
        stop_page = len(doc) - 1

    # Loop over pages 0 to stop_page (inclusive)
    for i in range(stop_page + 1):
        page = doc[i]
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        header_rects = get_header_rects(page, headers)
        if not header_rects:
            continue

        header_top_y = get_header_top_y(header_rects)

        # If we are on the page where "final balance" was found, overwrite table_bottom_y
        if saldo_finale_info is not None and i == saldo_finale_info[0]:
            table_bottom_y = saldo_finale_info[1].y1 + 5

        y_top_rl, y_bottom_rl = convert_to_reportlab_coords(header_top_y, table_bottom_y, page_height)

        overlay_packet = draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl, line_widths)
        merge_overlay(reader, writer, overlay_packet, i)

    output_pdf = generate_column_file_path()

    with open(output_pdf, "wb") as f:
        writer.write(f)


def find_saldo_finale(doc):
    """
    Finds "saldo finale" or "saldo fine" in the document.

    Parameters:
    doc (Document): The MuPDF document object.

    Returns:
    tuple or None: The page index and the rectangle of the first occurrence, or None if not found.
    """
    for i in range(len(doc) - 1, -1, -1):
        page = doc[i]
        saldo_rects = page.search_for("saldo finale")

        if not saldo_rects:
            saldo_rects = page.search_for("saldo fine")

        if saldo_rects:
            return i, saldo_rects[0]

    return None


# Section dedicated to processing files from Credem

def handle_credem_file(header, input_path):
    """
    Processes Credem bank files.

    Parameters:
    header (list): The header of the table.
    input_path (str): Path to the input PDF file.
    """
    y_bottom = 813
    x_coords = [35, 560]
    line_widths= [5, 5]

    draw_column_lines_on_pdf(header, x_coords, y_bottom, input_path, line_widths)

def extract_left_column_data(pdf_path_with_columns):
    """
    Extracts text from the left column of the table.

    Parameters:
    pdf_path_with_columns (str): Path to the PDF file with columns.

    Returns:
    list: A list of text extracted from the left column.
    """
    doc = fitz.open(pdf_path_with_columns)
    left_column_data = []

    for page in doc:
        blocks = page.get_text("blocks")
        
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            if x0 < 100:
                left_column_data.append(text.strip())

    return left_column_data

def extract_dates_from_left_column(data):
    """
    Extracts dates from the left column data.

    Parameters:
    data (list): List of text data from the left column.

    Returns:
    list: A list of dates found in the data.
    """
    dates = []
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
    
    for item in data:
        columns = item.split()
        if columns and date_pattern.match(columns[0]):
            dates.append(columns[0])
    
    return dates

# Section dedicated to processing files from Crédit Agricole

def handle_credit_agricole(header, input_path):    
    """
    Processes Credit Agricole bank files.

    Parameters:
    header (list): The header of the table.
    input_path (str): Path to the input PDF file.
    """
    y_bottom = 750
    x_coords = [21, 64, 115, 176, 239, 526, 578]
    line_widths= [3]

    draw_column_lines_on_pdf(header, x_coords, y_bottom, input_path, line_widths)

