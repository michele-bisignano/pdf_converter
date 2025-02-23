# The code in this file is responsible for reading the PDF file and generating the XLXS file.
import sys
import pandas as pd
from generalFunctions import find_substring_in_array, max_row_length, pdf_reader, find_any_word_in_array, switch_columns, switch_cell, transform_column_to_numbers, swap_elements
from pdf_modifier import handle_exceptional_layouts

def pdf_to_excel_converter_main(input_path, output_path):
    """
    Main function to convert PDF data to an Excel file.
    
    Parameters:
    input_path (str): Path to the input PDF file.
    output_path (str): Path to the output Excel file.
    """
    data = pdf_reader(input_path)

    if is_table_empty(data):
        print("\n\tERRORE: file illeggibile\n")
        sys.exit()

    header = find_row_with_data_and_descrizione(data)
    exceptional_table, header = handle_exceptional_layouts(header, input_path)

    if exceptional_table is not None:
        data = exceptional_table

    data = copy_table_from_saldo_iniziale(data)
    data = get_table_until_saldo_finale(data)

    if header:
        data = headers_delete(data, header)
        data = filter_table_by_header_length(data, header)
        data = filter_table_by_descrizione(data, header)
        data = fix_line_breaks(data, header)
        data, header = columns_switcher(data, header)
        df = pd.DataFrame(data, columns=header)
    else:
        df = pd.DataFrame(data, columns=max_row_length(data))

    try:
        df.to_excel(output_path, index=False)
        print(f"File Excel salvato in: {output_path}")
        check_table(data)
    except PermissionError:
        print("\n\tERRORE: chiudere la tabella Excel prima di eseguire l'algoritmo")

def is_table_empty(table):
    """
    Check if the table is empty.

    Parameters:
    table (list of lists): The table to check.

    Returns:
    bool: True if the table is empty, False otherwise.
    """
    if not table:
        return True
    for row in table:
        if row:
            return False
    return True

def find_row_with_data_and_descrizione(table):
    """
    Find the row containing "data" and "descrizione".

    Parameters:
    table (list of lists): The table to search.

    Returns:
    list: The row containing "data" and "descrizione", or an empty list if not found.
    """
    for row in table:
        if find_substring_in_array(row, "data") != -1 and find_substring_in_array(row, "descrizione") != -1:
            return row
    print("\n\tATTENZIONE: intestazione non trovata\n")
    return []

def copy_table_from_saldo_iniziale(table):
    """
    Return the part of the table starting from the row after "saldo iniziale" or "saldo precedente".

    Parameters:
    table (list of lists): The table to process.

    Returns:
    list of lists: The processed table.
    """
    for i, row in enumerate(table):
        if find_substring_in_array(row, "saldo iniziale") != -1 or find_substring_in_array(row, "saldo precedente") != -1:
            return table[i:]
    return table

def headers_delete(table, header):
    """
    Delete the headers from the table.

    Parameters:
    table (list of lists): The table to process.
    header (list): The header row.

    Returns:
    list of lists: The table without the headers.
    """
    return [row for row in table if not (find_substring_in_array(row, "descrizione") != -1 and find_substring_in_array(row, "data") != -1)]

def get_table_until_saldo_finale(table):
    """
    Return the table up to the final balance.

    Parameters:
    table (list of lists): The table to process.

    Returns:
    list of lists: The processed table.
    """
    for i in range(len(table) - 1, -1, -1):
        if find_substring_in_array(table[i], "saldo fin") != -1:
            return table[:i + 1]
    return table

def filter_table_by_descrizione(table, header):
    """
    Delete the rows with the description 'None'.

    Parameters:
    table (list of lists): The table to process.
    header (list): The header row.

    Returns:
    list of lists: The filtered table.
    """
    descrizione_index = find_substring_in_array(header, "descrizione")
    if descrizione_index == -1:
        print("Colonna DESCRIZIONE non trovata")
        return table
    return [row for row in table if row[descrizione_index] is not None]

def filter_table_by_header_length(table, header):
    """
    Delete rows that do not match the header length.

    Parameters:
    table (list of lists): The table to process.
    header (list): The header row.

    Returns:
    list of lists: The filtered table.
    """
    header_length = len(header)
    return [row for row in table if len(row) == header_length]

def fix_line_breaks(table, header):
    """
    Merge rows where 'data' is empty or None with the previous row's 'descrizione'.

    Parameters:
    table (list of lists): The table to process.
    header (list): The header row.

    Returns:
    list of lists: The processed table.
    """
    data_index = find_substring_in_array(header, "data")
    descrizione_index = find_substring_in_array(header, "descrizione")

    new_table = []
    if table:
        new_table.append(table[0])

    for i in range(1, len(table) - 1):
        row = table[i]
        data_value = row[data_index]
        if data_value is None or not str(data_value).strip():
            if new_table:
                new_table[-1][descrizione_index] += " " + row[descrizione_index]
            else:
                new_table.append(row)
        else:
            new_table.append(row)

    if len(table) > 1:
        new_table.append(table[-1])

    return new_table

def columns_switcher(table, header):
    """
    Rearrange the dataset columns.

    Parameters:
    table (list of lists): The table to process.
    header (list): The header row.

    Returns:
    tuple: The processed table and the updated header.
    """
    final_header_indexes = [0, 2, 5, 6]
    initial_header_indexes = []

    credit_aliases = ["dare", "entrate", "credito"]
    debit_aliases = ["avere", "uscite", "debito"]

    initial_header_indexes.append(find_substring_in_array(header, "data"))
    initial_header_indexes.append(find_substring_in_array(header, "descrizione"))
    initial_header_indexes.append(find_any_word_in_array(header, credit_aliases))
    initial_header_indexes.append(find_any_word_in_array(header, debit_aliases))

    for i in range(len(initial_header_indexes)):
        if initial_header_indexes[i] != -1:
            table = switch_columns(table, initial_header_indexes[i], final_header_indexes[i])
            header = switch_cell(header, initial_header_indexes[i], final_header_indexes[i])
            initial_header_indexes = swap_elements(initial_header_indexes, initial_header_indexes[i], final_header_indexes[i])

    if initial_header_indexes[2] != -1:
        table = transform_column_to_numbers(table, final_header_indexes[2])

    if initial_header_indexes[3] != -1:
        table = transform_column_to_numbers(table, final_header_indexes[3])

    return table, header

def check_table(table):
    """
    Check if the sum of incomes and expenses is equal to the final balance.

    Parameters:
    table (list of lists): The table to check.
    """
    credit_column_number = 5
    debit_column_number = 6

    credit_sum = 0
    debit_sum = 0

    try:
        for row in table[:-1]:
            credit_value = row[credit_column_number]
            debit_value = row[debit_column_number]
            if credit_value == '' or credit_value == "":
                credit_value = None
            if debit_value == '' or debit_value == "":
                debit_value = None

            if credit_value is not None:
                if isinstance(credit_value, (int, float)):
                    credit_sum += credit_value
                else:
                    raise ValueError(f"Invalid value in credit column: {credit_value}")
            else:
                if debit_value is not None:
                    if isinstance(debit_value, (int, float)):
                        debit_sum += debit_value
                    else:
                        raise ValueError(f"Invalid value in debit column: {debit_value}")
                else:
                    raise ValueError("Both credit and debit values are None")
    except ValueError as e:
        print("\n\tERRORE: La tabella non e' stata esportata correttamente")
        return

    debit_sum = abs(debit_sum)
    saldo_finale_calculated = credit_sum - debit_sum

    if saldo_finale_calculated > 0:
        saldo_finale_exported_table = table[-1][credit_column_number]
    else:
        saldo_finale_exported_table = table[-1][debit_column_number]

    saldo_finale_calculated = round(saldo_finale_calculated, 2)
    saldo_finale_calculated = abs(saldo_finale_calculated)

    if saldo_finale_exported_table is not None and isinstance(saldo_finale_exported_table, (int, float)):
        if saldo_finale_calculated == saldo_finale_exported_table:
            print("La tabella e' stata esportata correttamente")
        else:
            print("\n\tERRORE: la tabella NON e' stata esportata correttamente")
            print(f"Saldo mancante: {saldo_finale_exported_table - saldo_finale_calculated}")
    else:
        print("\n\tERRORE: Non e' stato trovato il saldo finale")

    


