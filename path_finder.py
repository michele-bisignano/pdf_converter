"""
This file contains all the necessary functions for file management, 
including finding the paths for input and output files, generating paths 
for temporary files, and handling the deletion of existing files.
"""

import os
import sys

def input_file_path_finder():
    """
    Returns the path of the single PDF file in the script's directory.
    If there are no PDF files or more than one, it prints an error and exits.
    """
    # Delete the column file PDF if it exists
    delete_pdf(generate_column_file_path())

    # Get the absolute path of the script's directory
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Find all PDF files in the directory
    pdf_files = [
        os.path.join(current_directory, file)
        for file in os.listdir(current_directory)
        if file.lower().endswith('.pdf')
    ]

    # Check if there is exactly one PDF file
    if len(pdf_files) != 1:
        if len(pdf_files) > 1:
            print(f"\n\tERROR: There are {len(pdf_files)} PDF files in the folder.")
            print("\tRemove the excess PDF files and try again.\n")
        else:
            print(f"\n\tERROR: No PDF files found in the directory '{current_directory}'.\n")
        input("Press Enter to exit...")
        sys.exit()

    return pdf_files[0]

def output_file_path_generator():
    """
    Generates the output file path for the Excel file to be created.
    """
    # Get the absolute path of the script's directory
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Combine the directory path with the output file name
    output_path = os.path.join(current_directory, "DA_IMPORTARE.xlsx")

    return output_path

def generate_column_file_path():
    """
    Generates the file path for the temporary PDF file used to create columns.
    """
    # Get the absolute path of the script's directory
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Combine the directory path with the column file name
    column_file_path = os.path.join(current_directory, "columns_file.pdf")

    return column_file_path

def delete_pdf(file_path):
    """
    Deletes the specified file if it exists.
    """
    if os.path.exists(file_path):
        os.remove(file_path)