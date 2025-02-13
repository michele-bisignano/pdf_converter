# This file contains functions to handle Credem and Credit_Agricole pdf

from generalFunctions import destroy_pdf

# Check if the table belongs to Credem or Crédit Agricole bank.
def handle_exceptional_layouts(header, input_path):
	# if the table doesn't belong to Credem or Crédit Agricole bank the function returns none
	table=None
	credem_header= [None, 'DATA VALUTA', 'DESCRIZIONE OPERAZIONE', 'IMPORTO A DEBITO', None]
	credit_agricole_header=["Data", "Valuta", "Movimenti dare", "Movimenti avere", "Descrizione operazioni", "Riferimenti"]
	
	pdf_path_with_columns = "./output_with_columns.pdf"

	if(header == credem_header):
		table = handle_credem_file(header, input_path)
		header=  ["DATA CONTABILE", "DATA VALUTA", "DESCRIZIONE OPERAZIONE", "IMPORTO A DEBITO", "IMPORTO A CREDITO"]

	elif (header == credit_agricole_header):
		table = handle_credit_agricole(header, input_path)
	
	destroy_pdf(pdf_path_with_columns)

	return table

# Draws a vertical line on the canvas for each x in x_coords, the lines extend from y_top to y_bottom.
def draw_columns(x_coords, y_top, y_bottom, canvas_obj, line_width=1):
   
    offset = -2  # Slightly shift the lines to the left
    canvas_obj.setLineWidth(line_width)
    for x in x_coords:
        canvas_obj.line(x + offset, y_top, x + offset, y_bottom)



# CREDEM function

def handle_credem_file(header, input_path):


	return table

# CREDIT AGRICOLE functions:

def handle_credit_agricole(header, input_path):


	return table


