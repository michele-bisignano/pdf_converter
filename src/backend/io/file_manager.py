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
    script_dir = os.path.dirname(os.path.abspath(__file__))  # src/backend/io/
    return os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))  # root


def _find_pdfs(directory):
    """Returns list of PDF file paths in the given directory."""
    return [
        os.path.join(directory, file)
        for file in os.listdir(directory)
        if file.lower().endswith('.pdf')
    ]


def input_file_path_finder():
    """
    Returns the path of the single PDF file found in the project root
    or src/ directory. If not exactly one exists across both, errors.
    """
    delete_pdf(generate_column_file_path())

    root = _get_project_root()
    src_dir = os.path.join(root, "src")

    pdf_files = _find_pdfs(root)
    if os.path.isdir(src_dir):
        pdf_files += _find_pdfs(src_dir)

    if len(pdf_files) != 1:
        if len(pdf_files) > 1:
            print("\n\tERROR: {} PDF files found between root and src/.".format(len(pdf_files)))
            print("\tRemove the extra PDF files and try again.\n")
        else:
            print("\n\tERROR: No PDF file found in root or src/.\n")
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
