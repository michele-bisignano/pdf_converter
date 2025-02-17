# This file contains the functions that return the input_path and output_path.
import os
import sys

# It returns the paths of the PDF files present in the same directory as the script.
def input_file_path_finder():
    
    # Deletes the pdf with column file if exists
    delete_pdf(generate_column_file_path())

    # It gets the absolute path of the script's folder
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Filter the PDF files present in the folder
    file_pdf = [
        os.path.join(current_directory, file)
        for file in os.listdir(current_directory)
        if file.lower().endswith('.pdf')
    ]
    
    if len(file_pdf) != 1:
        if len(file_pdf)>1:
            print(f"\n\tERRORE: sono presenti {len(file_pdf)} file pdf nella cartella")
            print("\trimuovere i file PDF in eccesso e riprovare.\n")
        else:
            print("\n\ERRORE: Nessun file PDF trovato.\n")

        sys.exit()

    return file_pdf[0]

# TOGLIERE SE NON USATO
def temp_support_file_path_finder():

	# It gets the absolute path of the script's directory
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Combine the folder with the temporary file name
    file_name = "dati_temporanei.xlsx"
    path = os.path.join(current_directory, file_name)
    
    return path

def output_file_path_generator():

    # It gets the absolute path of the script's folder
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Combine the folder with the temporary file name
    path = os.path.join(current_directory, "DA_IMPORTARE.xlsx")

    return path

# This function generates the file path of a document where columns are automatically created
def generate_column_file_path():
    # It gets the absolute path of the script's folder
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Combine the folder with the temporary file name
    path = os.path.join(current_directory, "columns_file.pdf")
    return path

# Deletes the file
def delete_pdf(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)