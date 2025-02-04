# This file contains the functions that return the input_path and output_path.
import os
import sys

# It returns the paths of the PDF files present in the same directory as the script.
def input_file_path_finder():

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

    return file_pdf

def temp_support_file_path_finder():

	# It gets the absolute path of the script's directory
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Combine the folder with the temporary file name
    nome_file = "dati_temporanei.xlsx"
    percorso_file = os.path.join(current_directory, nome_file)
    
    return percorso_file

def output_file_path_generator():

    # It gets the absolute path of the script's folder
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Combine the folder with the temporary file name
    percorso_file = os.path.join(current_directory, "DA_IMPORTARE.xlsx")

    return percorso_file

