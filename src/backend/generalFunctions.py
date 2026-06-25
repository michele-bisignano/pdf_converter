# This file contains reusable functions that are utilized in multiple parts of the project.  
import pdfplumber

def find_substring_in_array(array, search_string):
    """
    Returns the index of the first occurrence of search_string in array.
    The search is case-insensitive.

    Parameters:
    array (list): The list of strings to search.
    search_string (str): The string to search for.

    Returns:
    int: The index of the first occurrence found, or -1 if no match is found.
    """
    search_string = search_string.lower()
    for index, element in enumerate(array):
        if element and search_string in element.lower():
            return index
    return -1

def find_any_word_in_array(array, search_string_array):
    """
    Searches array for any substring matching a word in search_string_array.

    Parameters:
    array (list): The list of strings to search.
    search_string_array (list): The list of strings to search for.

    Returns:
    int: The index of the first occurrence found, or -1 if no match is found.
    """
    for word in search_string_array:
        idx = find_substring_in_array(array, word)
        if idx != -1:
            return idx
    return -1

def max_row_length(table):
    """
    Finds the length of the longest row in the table.

    Parameters:
    table (list of lists): The table to search.

    Returns:
    int: The length of the longest row.
    """
    return max(len(row) for row in table)

def words_counter(text):
    """
    Returns the number of words in the text.

    Parameters:
    text (str): The text to count words in.

    Returns:
    int: The number of words.
    """
    return len(text.split())

def pdf_reader(pdf_path):
    """
    Reads the PDF and extracts tables.

    Parameters:
    pdf_path (str): The path to the PDF file.

    Returns:
    list of lists: The extracted table data.
    """
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        data.append(row)
    return data

def switch_cell(array, cell1, cell2):
    """
    Switches the contents of two cells in an array.

    Parameters:
    array (list): The list containing the cells.
    cell1 (int): The index of the first cell.
    cell2 (int): The index of the second cell.

    Returns:
    list: The array with the cells switched.
    """
    if cell1 == cell2:
        return array

    max_index = max(cell1, cell2)
    if max_index >= len(array):
        array.extend([None] * (max_index + 1 - len(array)))
    
    array[cell1], array[cell2] = array[cell2], array[cell1]
    return array

def swap_elements(array, element1, element2):
    """
    Switches the contents of two cells in an array if element2 is after element1.

    Parameters:
    array (list): The list containing the elements.
    element1 (any): The first element.
    element2 (any): The second element.

    Returns:
    list: The array with the elements switched, if needed.
    """
    if element1 in array and element2 in array:
        index1 = array.index(element1)
        index2 = array.index(element2)
        if index2 > index1:
            array = switch_cell(array, index1, index2)
    return array

def transform_column_to_numbers(table, column_number):
    """
    Transforms all numbers in a specific column of the table from strings with commas to numeric types.

    Parameters:
    table (list of lists): The table containing the data.
    column_number (int): The index of the column to transform.

    Returns:
    list of lists: The table with the transformed column.
    """
    new_table = []
    for row in table:
        new_row = row[:]
        try:
            if isinstance(new_row[column_number], str):
                value = new_row[column_number].replace(' ', '')
                is_negative = value.startswith('-')
                if is_negative:
                    value = value[1:]
                value = value.replace('.', '').replace(',', '.')
                if value.replace('.', '', 1).isdigit():
                    new_value = float(value) if '.' in value else int(value)
                    if is_negative:
                        new_value *= -1
                    new_row[column_number] = new_value
                else:
                    raise ValueError
        except (IndexError, ValueError):
            new_row = row
        new_table.append(new_row)
    return new_table

def switch_columns(table, index_col1, index_col2):
    """
    Switches the contents of two columns in a 2D array.

    Parameters:
    table (list of lists): The table containing the data.
    index_col1 (int): The index of the first column.
    index_col2 (int): The index of the second column.

    Returns:
    list of lists: The table with the columns switched.
    """
    if index_col1 == index_col2:
        return table

    max_col = max(index_col1, index_col2)
    for row in table:
        while len(row) <= max_col:
            row.append('')
    
    col1_data = column_reader(table, index_col1)
    col2_data = column_reader(table, index_col2)
    
    table = column_writer(table, index_col1, col2_data)
    table = column_writer(table, index_col2, col1_data)
    
    return table

def column_reader(table, col_index):
    """
    Reads the col_index column from the table.

    Parameters:
    table (list of lists): The table containing the data.
    col_index (int): The index of the column to read.

    Returns:
    list: The data from the specified column.
    """
    column_data = []
    for row in table:
        if col_index < len(row):
            column_data.append(row[col_index])
        else:
            column_data.append('')
    return column_data

def column_writer(table, col_index, data_column, start_row=0):
    """
    Writes the data_column to the col_index column in the table.

    Parameters:
    table (list of lists): The table containing the data.
    col_index (int): The index of the column to write to.
    data_column (list): The data to write to the column.
    start_row (int, optional): The row index to start writing from. Defaults to 0.

    Returns:
    list of lists: The table with the written column.
    """
    max_rows = min(len(table), len(data_column) + start_row)
    while len(table) < max_rows:
        table.append([''] * (col_index + 1))
    
    data_index = 0
    for row_index in range(start_row, len(table)):
        if data_index >= len(data_column):
            break
        row = table[row_index]
        if any("data" in cell.lower() for cell in row if cell):
            continue
        while len(row) <= col_index:
            row.append('')
        row[col_index] = data_column[data_index]
        data_index += 1
    
    return table