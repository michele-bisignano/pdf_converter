# This file contains functions to handle Credem and Credit_Agricole pdf
import io
import fitz  # PyMuPDF
import re
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from generalFunctions import pdf_reader, column_writer
from path_finder import generate_column_file_path, delete_pdf

# Check if the table belongs to Credem or Crédit Agricole bank.
def handle_exceptional_layouts(header, input_path):
    # If the table does not belong to Credem or Crédit Agricole bank, the function returns None
    table = None

    # Define the expected header for Credem bank
    credem_header = [None, 'DATA VALUTA', 'DESCRIZIONE OPERAZIONE', 'IMPORTO A DEBITO', None]

    # Define the expected header for Crédit Agricole bank
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

        all_table = extract_left_column_data(pdf_path_with_columns) # Extract the data from the document
        left_column_data= extract_dates_from_left_column(all_table) # Extract the dates from the left column
        table= column_writer(table, 0, left_column_data) # Write the dates back to the table

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



# Draws a vertical line on the canvas for each x in x_coords, the lines extend from y_top to y_bottom.
def draw_columns(x_coords, y_top, y_bottom, canvas_obj, line_widths, default_line_width=1):
    
    diff = len(x_coords) - len(line_widths)
    
    for i, x in enumerate(x_coords):
        if i < diff:
            lw = default_line_width
        else:
            lw = line_widths[i - diff]
        canvas_obj.setLineWidth(lw)
        canvas_obj.line(x, y_top, x , y_bottom)

# Returns the highest y-coordinate among the header rectangles
def get_header_top_y(header_rects):
    
    return min(rect.y0 for rect in header_rects.values())

# Finds the headers rects
def get_header_rects(page, headers):
    header_rects = {}
    for header in headers:
        rects = page.search_for(header)
        if rects:
            header_rects[header] = rects[0]
    return header_rects

# Creates an overlay with ReportLab to draw the columns
def draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl, line_widths):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    c.setStrokeColorRGB(0, 0, 0)  # Set the line color (black)
    draw_columns(x_coords, y_top_rl, y_bottom_rl, c, line_widths)
    c.save()
    packet.seek(0)
    return packet

# Merges the overlay with the original page using PyPDF2
def merge_overlay(reader, writer, overlay_packet, page_index):
    overlay_pdf = PdfReader(overlay_packet)
    overlay_page = overlay_pdf.pages[0]
    
    page_to_merge = reader.pages[page_index]
    page_to_merge.merge_page(overlay_page)
    writer.add_page(page_to_merge)

# Converts coordinates from MuPDF to ReportLab (bottom left origin)
def convert_to_reportlab_coords(header_top_y, table_bottom_y, page_height):
    y_top_rl = page_height - header_top_y
    y_bottom_rl = page_height - table_bottom_y
    return y_top_rl, y_bottom_rl

# Main function that draws columns on each page of the PDF
def draw_column_lines_on_pdf(headers, x_coords, table_bottom_y, input_pdf, line_widths):
    doc = fitz.open(input_pdf)
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
   # Find the first occurrence of "final balance" (or "saldo fine") starting from the last page
    saldo_finale_info = find_saldo_finale(doc)
    # saldo_finale_info is a tuple (page_index, rect) or None

    # Determine the last page to process:
    if saldo_finale_info is not None:
        # If found, process pages from 0 up to and including the page where "final balance" is found
        stop_page = saldo_finale_info[0]
    else:
        # If not found, process all pages in the document
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
            # Set the bottom of the table to the bottom edge of the word "final balance"
            table_bottom_y = saldo_finale_info[1].y1+5

        y_top_rl, y_bottom_rl = convert_to_reportlab_coords(header_top_y, table_bottom_y, page_height)
        
        overlay_packet = draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl, line_widths)
        merge_overlay(reader, writer, overlay_packet, i)

    output_pdf = generate_column_file_path()

    with open(output_pdf, "wb") as f:
        writer.write(f)

# Finds "saldo finale"
def find_saldo_finale(doc):
    # Iterate over the pages in reverse order
    for i in range(len(doc) - 1, -1, -1):
        page = doc[i]
        # Search for "saldo finale" on the current page
        saldo_rects = page.search_for("saldo finale")
        
        # If "saldo finale" is not found, search for "saldo fine"
        if not saldo_rects:
            saldo_rects = page.search_for("saldo fine")
        
        # If any occurrence is found, return the page index and the first found rectangle
        if saldo_rects:
            return i, saldo_rects[0]
    
    # Return None if neither "saldo finale" nor "saldo fine" is found in the document
    return None


# CREDEM functions:

def handle_credem_file(header, input_path):

    y_bottom = 813  # How far the columns should extend
    x_coords = [35, 560]  #  X-coordinates of the columns 
    line_widths= [5,5]

    draw_column_lines_on_pdf(header, x_coords, y_bottom, input_path, line_widths)

 # Extract text from the table
def extract_left_column_data(pdf_path_with_columns):
    # Open the PDF file
    doc = fitz.open(pdf_path_with_columns)
    left_column_data = []

    for page in doc:
        # Extract all the text blocks from the page
        blocks = page.get_text("blocks")
        
        # Identify the left column blocks based on their x-coordinates
        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block
            # Assuming the left column has x-coordinates less than a certain threshold (e.g., 100)
            if x0 < 100:
                left_column_data.append(text.strip())

    return left_column_data

# Extract data from the left column
def extract_dates_from_left_column(data):
    # Initialize an empty list to store the dates
    dates = []
    
    # Regular expression to find dates in the format DD/MM/YYYY
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
    
    # Iterate over each item in the data list
    for item in data:
        # Split the item by spaces to separate potential columns
        columns = item.split()
        
        # Check if the first column contains a date
        if columns and date_pattern.match(columns[0]):
            # Add the date from the first column to the dates list
            dates.append(columns[0])
    
    return dates

# CREDIT AGRICOLE functions:

def handle_credit_agricole(header, input_path):    
    y_bottom = 750  # How far the columns should extend
    x_coords = [21, 64, 115, 176, 239, 526, 578]  #  X-coordinates of the columns 
    line_widths= [3]

    draw_column_lines_on_pdf(header, x_coords, y_bottom, input_path, line_widths)

    pdf_path_with_columns = generate_column_file_path()


