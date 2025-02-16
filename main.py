# main file
from pdf_to_exel_converter import pdf_to_exel_converter_main
from path_finder import input_file_path_finder, output_file_path_generator

def main():
	input_path=input_file_path_finder();
	output_path= output_file_path_generator();

	pdf_to_exel_converter_main(input_path, output_path)

	print("\nFile esporato.\n")


main()
