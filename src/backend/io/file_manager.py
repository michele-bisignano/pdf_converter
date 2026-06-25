"""
This file contains all the necessary functions for file management,
including finding the paths for input and output files, generating paths
for temporary files, and handling the deletion of existing files.
"""

import os
import sys


def _get_project_root():
    """Returns the project root directory (parent of src/)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    script_dir = os.path.dirname(os.path.abspath(__file__))  # src/backend/
    return os.path.dirname(os.path.dirname(script_dir))  # root


def input_file_path_finder():
    """
    Returns the path of the single PDF file in the project root.
    If there are no PDF files or more than one, it prints an error and exits.
    """
    delete_pdf(generate_column_file_path())

    current_directory = _get_project_root()

    pdf_files = [
        os.path.join(current_directory, file)
        for file in os.listdir(current_directory)
        if file.lower().endswith('.pdf')
    ]

    if len(pdf_files) != 1:
        if len(pdf_files) > 1:
            print(f"\n\tERRORE: Sono presenti {len(pdf_files)} file PDF nella cartella.")
            print("\tRimuovi i file PDF in eccesso e riprova.\n")
        else:
            print(f"\n\tERRORE: Nessun file PDF trovato nella directory '{current_directory}'.\n")
        input("Press Enter to exit...")
        sys.exit()

    return pdf_files[0]


def output_file_path_generator():
    """Generates the output Excel file path in the project root."""
    return os.path.join(_get_project_root(), "DA_IMPORTARE.xlsx")


def generate_column_file_path():
    """Generates the path for the temporary PDF column file in the project root."""
    return os.path.join(_get_project_root(), "columns_file.pdf")


def delete_pdf(file_path):
    """Deletes the specified file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
