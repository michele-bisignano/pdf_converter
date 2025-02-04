# main file
from pdf_to_exel_converter import pdf_to_exel_converter_commercialisti_function
from file_path_finder import input_file_path_finder, temp_support_file_path_finder, output_file_path_generator

def main():
	input_path=input_file_path_finder();
	temp_support_path= temp_support_file_path_finder();
	output_path= output_file_path_generator();

	pdf_to_exel_converter_commercialisti_function(input_path, temp_support_path)

	print("\nFile esporato correttamente.\n")


main()
