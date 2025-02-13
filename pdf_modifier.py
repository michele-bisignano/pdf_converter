# This file contains functions to handle Credem and Credit_Agricole pdf
import io
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from generalFunctions import destroy_pdf, pdf_reader
from path_finder import generate_column_file_path

# Check if the table belongs to Credem or Crédit Agricole bank.
def handle_exceptional_layouts(header, input_path):
	# if the table doesn't belong to Credem or Crédit Agricole bank the function returns none
	table=None
	credem_header= [None, 'DATA VALUTA', 'DESCRIZIONE OPERAZIONE', 'IMPORTO A DEBITO', None]
	credit_agricole_header=["Data", "Valuta", "Movimenti dare", "Movimenti avere", "Descrizione operazioni", "Riferimenti"]
	
	pdf_path_with_columns = generate_column_file_path()

	if(header == credem_header):        
		header=  ["DATA CONTABILE", "DATA VALUTA", "DESCRIZIONE OPERAZIONE", "IMPORTO A DEBITO", "IMPORTO A CREDITO"]
		handle_credem_file(header, input_path)

	elif (header == credit_agricole_header):
		handle_credit_agricole(header, input_path)
	
	destroy_pdf(pdf_path_with_columns)

	return table

# Draws a vertical line on the canvas for each x in x_coords, the lines extend from y_top to y_bottom.
def draw_columns(x_coords, y_top, y_bottom, canvas_obj, line_width=1):
   
    offset = -2  # Slightly shift the lines to the left
    canvas_obj.setLineWidth(line_width)
    for x in x_coords:
        canvas_obj.line(x + offset, y_top, x + offset, y_bottom)

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
def draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    c.setStrokeColorRGB(1, 0, 0)  # Set the line color (red)
    draw_columns(x_coords, y_top_rl, y_bottom_rl, c)
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
def draw_column_lines_on_pdf(headers, x_coords, table_bottom_y, input_pdf):
    doc = fitz.open(input_pdf)
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Find the first occurrence of "final balance" starting from the last page
    saldo_finale_info = find_saldo_finale(doc)
    # final_balance_info is a tuple (page_index, rect) or None

    for i in range(len(doc)):
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
            table_bottom_y = saldo_finale_info[1].y1

        y_top_rl, y_bottom_rl = convert_to_reportlab_coords(header_top_y, table_bottom_y, page_height)
        
        overlay_packet = draw_overlay(page_width, page_height, x_coords, y_top_rl, y_bottom_rl)
        merge_overlay(reader, writer, overlay_packet, i)

    output_pdf = generate_column_file_path()

    with open(output_pdf, "wb") as f:
        writer.write(f)


# CREDEM function

def handle_credem_file(header, input_path):




	return table

# CREDIT AGRICOLE functions:

def handle_credit_agricole(header, input_path):    
    y_bottom = 750  # How far the columns should extend
    x_coords = [23, 66, 117, 178, 241, 528, 578]  #  X-coordinates of the columns 

    draw_column_lines_on_pdf(header, x_coords, y_bottom, input_path)

    pdf_path_with_columns = generate_column_file_path()
    table = pdf_reader(pdf_path_with_columns)

    return table

# Finds "saldo finale"
def find_saldo_finale(doc):
    
    for i in range(len(doc) - 1, -1, -1):
        page = doc[i]
        saldo_rects = page.search_for("saldo finale")
        if saldo_rects:
            # Finds the first occurrence found on the page
            return i, saldo_rects[0]
    return None


