#This file contains functions that can be useful anywhere.

import os

# Returns the index of the first occurrence found
def find_substring_in_array(array, search_string):
    search_string = search_string.lower()  # To make the search case-insensitive
    for index, element in enumerate(array):
        if element:
            # Compares if the search_string is contained within the element (case-insensitive)
            if search_string in element.lower():
                return index  # Returns the index of the first occurrence found
    return -1  # Returns -1 if no match is found


# Finds the length of the longest row
def max_row_length(table):    
    max_length = max(len(row) for row in table)
    return max_length

# Returns the number of word in the array
def words_counter(testo):
    parole = testo.split()
    return len(parole)


#  Deletes the PDF file located at pdf_path if it exists
def destroy_pdf(pdf_path):

    if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
        try:
            os.remove(pdf_path)
        except Exception as e:
            print(f"An error occurred while deleting the file: {e}")
