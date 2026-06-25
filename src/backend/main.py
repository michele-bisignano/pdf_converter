# main file
from pdf_to_exel_converter import pdf_to_excel_converter_main
from path_finder import input_file_path_finder, output_file_path_generator

def main():
    """
    Main function to convert a PDF file to an Excel file.

    It finds the input PDF file path, generates the output Excel file path,
    and then calls the converter function.
    """
    # Find the input PDF file path
    input_path = input_file_path_finder()

    # Generate the output Excel file path
    output_path = output_file_path_generator()

    # Convert the PDF to Excel
    pdf_to_excel_converter_main(input_path, output_path)

    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
