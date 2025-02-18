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

# Switch the contents of two cells in an array
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

#  Transforms all numbers in a specific column (column_number) of the table (2D array) from strings with commas to numeric types
def transform_column_to_numbers(table, column_number):

    new_table = []

    for row in table:
        new_row = row[:]
        try:
            if isinstance(new_row[column_number], str):
                # Check for negative sign
                is_negative = new_row[column_number].startswith('-')
                if is_negative:
                    new_row[column_number] = new_row[column_number][1:]  # Remove the negative sign
                # Remove periods used as thousand separators
                new_row[column_number] = new_row[column_number].replace('.', '')
                # Replace comma with a period for conversion
                new_row[column_number] = new_row[column_number].replace(',', '.')
                # Check if the string is a number
                if new_row[column_number].replace('.', '', 1).isdigit():
                    new_row[column_number] = float(new_row[column_number]) if '.' in new_row[column_number] else int(new_row[column_number])
                    if is_negative:
                        new_row[column_number] *= -1
                else:
                    # Restore the comma and periods in the original string if it's not a number
                    new_row[column_number] = row[column_number]
        except (IndexError, ValueError):
            # Ignore index or conversion errors
            pass
        new_table.append(new_row)


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
