#This file contains functions that can be useful anywhere.

from operator import index
import pdfplumber
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

# Searches array1 for any substring matching a word in search_string_array
def find_any_word_in_array(array, search_string_array):

    for word in search_string_array:
        idx = find_substring_in_array(array, word)
        if idx != -1:
            return idx
    return -1


# Finds the length of the longest row
def max_row_length(table):    
    max_length = max(len(row) for row in table)
    return max_length

# CONTROLLA SE USATA
# Returns the number of word in the array
def words_counter(testo):
    parole = testo.split()
    return len(parole)

# Read the pdf
def pdf_reader(pdf_path):
     # Create a list to collect the data
    data = []

    # open PDF file
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract the tables
            tables = page.extract_tables()
        
            # Check if there are tables on the page.
            if tables:
                for table in tables:
                    for row in table:
                        data.append(row)

    return data

# Switch the contents of two cells in an array, cell1 and cell2 are the indexes of the cells to switch
def switch_cell(array, cell1, cell2):

    if (cell1 == cell2):
        return array

    max_index = max(cell1, cell2)
    
    # Expand the array if necessary
    if max_index >= len(array):
        array.extend([None] * (max_index + 1 - len(array)))
    
    # Swap the contents of cell1 and cell2
    array[cell1], array[cell2] = array[cell2], array[cell1]
    
    return array

# Switch the contents of two cells in an array if element2 is after than element1
# element1 and element2 are the elements to switch (not their indexes)
def swap_elements(array, element1, element2):
    if element1 in array and element2 in array:
        index1 = array.index(element1)
        index2 = array.index(element2)
        if index2 > index1:
            array = switch_cell(array, index1, index2)
            return array
    return array

#  Transforms all numbers in a specific column (column_number) of the table (2D array) from strings with commas to numeric types
def transform_column_to_numbers(table, column_number):
    new_table = []

    for row in table:
        new_row = row[:]
        try:
            if isinstance(new_row[column_number], str):
                value = new_row[column_number]

                # Remove spaces within the number
                value = value.replace(' ', '')

                # Check for negative sign
                is_negative = value.startswith('-')
                if is_negative:
                    value = value[1:]  # Temporarily remove the negative sign

                # Remove periods used as thousand separators
                value = value.replace('.', '')

                # Replace comma with a period for decimal conversion
                value = value.replace(',', '.')

                # Check if the string is a valid number
                if value.replace('.', '', 1).isdigit():
                    new_value = float(value) if '.' in value else int(value)

                    # Reapply the negative sign if needed
                    if is_negative:
                        new_value *= -1

                    new_row[column_number] = new_value  # Assign the converted value
                else:
                    raise ValueError  # Force an error if the value is not a valid number
        except (IndexError, ValueError):
            new_row = row  # Restore the original row in case of an error

        new_table.append(new_row)  # Add the row to the table after processing

    return new_table

# FUNCTIONS FOR SWITCH THE COLUMNS:

# Switch the contents of two columns in a 2D array
def switch_columns(table, index_col1, index_col2):

    if index_col1 == index_col2:
        return table

    # Ensure the table has enough columns
    max_col = max(index_col1, index_col2)
    for row in table:
        while len(row) <= max_col:
            row.append('')
    
    # Read the columns
    col1_data = column_reader(table, index_col1)
    col2_data = column_reader(table, index_col2)
    
    # Write the columns back in switched positions
    table = column_writer(table, index_col1, col2_data)
    table = column_writer(table, index_col2, col1_data)
    
    return table

# Read the col_index column from the table (2D array).
def column_reader(table, col_index):

    column_data = []
    for row in table:
        if col_index< len(row):
            column_data.append(row[col_index])
        else:
            column_data.append('')
    return column_data

# Write the data_column to the col_index column in the table (2D array).
def column_writer(table, col_index, data_column):
    # Find the index of the row containing "saldo precedente"
    start_row = find_substring_in_array([" ".join(filter(None, row)) for row in table], "saldo precedente")
    if start_row == -1:
        start_row = 0  # If "saldo precedente" is not found, start from the first row
    else:
        start_row += 1  # Start from the row after "saldo precedente"
    
    max_rows = min(len(table), len(data_column) + start_row)
    
    # Ensure the table has enough rows
    while len(table) < max_rows:
        table.append([''] * (col_index + 1))
    
    # Write the data to the specified column starting from start_row
    data_index = 0
    for row_index in range(start_row, len(table)):
        if data_index >= len(data_column):
            break
        row = table[row_index]
        
        # Skip rows that contain the word "data"
        if any("data" in cell.lower() for cell in row if cell):
            continue
        
        while len(row) <= col_index:
            row.append('')
        row[col_index] = data_column[data_index]
        data_index += 1
    
    return table
