"""CLI entry point for PDF to Excel conversion."""
import logging
from src.backend.io.file_manager import input_file_path_finder, output_file_path_generator
from src.backend.pdf_to_exel_converter import pdf_to_excel_converter_main

logger = logging.getLogger("pdf_converter.cli")


def main():
    """
    Convert a PDF file to an Excel file.

    Finds the input PDF file path, generates the output Excel file path,
    and calls the converter function.

    Returns:
        None
    """
    input_path = input_file_path_finder()
    output_path = output_file_path_generator()
    result = pdf_to_excel_converter_main(input_path, output_path)

    if result:
        logger.info("Conversion result: %s", result)
        if not result.get("success"):
            logger.warning("Conversion did not succeed")
        if result.get("warning"):
            logger.warning(result.get("warning_message", ""))

    try:
        input("Press Enter to exit...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
