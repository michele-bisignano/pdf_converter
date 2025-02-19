# Export the PDF file to an XLSX to be arranged
#from asyncio.windows_events import NULL
import sys
from tabnanny import check
import pandas as pd
from generalFunctions import find_substring_in_array, max_row_length, pdf_reader, find_any_word_in_array, switch_columns, switch_cell, transform_column_to_numbers, swap_elements
from pdf_modifier import handle_exceptional_layouts

def pdf_to_exel_converter_main(input_path, output_path):
    
    # Set the path for the PDF and output Excel file
    pdf_path = input_path
    output1_excel_path = output_path

    data = pdf_reader(pdf_path)

    if(is_table_empty(data)):
        print("\n\tERRORE: file illeggibile\n")
        sys.exit()

    header= find_row_with_data_and_descrizione(data)

    exceptional_table, header=handle_exceptional_layouts(header, input_path)

    if(exceptional_table != None):
         data=exceptional_table
    
    data = copy_table_from_saldo_iniziale(data)
    data = get_table_until_saldo_finale(data)


    if(header!=[]):

        data = headers_delete(data, header)        
        data = filter_table_by_header_length(data, header)
        data = filter_table_by_descrizione(data, header)
        data = fix_line_breaks(data, header)
        data, header = columns_switcher(data, header)

        df = pd.DataFrame(data, columns=header)
    
    else:
        df=pd.DataFrame(data, columns=max_row_length(data))

    try:
        # Save the DataFrame to an Excel file
        df.to_excel(output1_excel_path, index=False)
        print(f"File Excel salvato in: {output1_excel_path}")        
        check_table(data)
    except PermissionError:
        print("\n\tERRORE: chiudere la tabella Excel prima di eseguire l'algoritmo")


# Check if the table is empty
def is_table_empty(table):
    if not table:  # check if the table is empty
        return True
    for row in table:
       if row:  # check if the row is empty
            return False
    return True

#It returns the array corresponding to the header
def find_row_with_data_and_descrizione(table):

    for row in table:
        if((find_substring_in_array(row, "data")!=-1) and (find_substring_in_array(row, "descrizione")!=-1)):
            return row  # Return the first row that satisfies both conditions
    
    print("\n\tATTENTIONE: intestazione non trovata\n")
    # No matching row found
    return []

# It returns the part of the table starting from the row after the header
def copy_table_from_saldo_iniziale(table):
     for i, row in enumerate(table):
        if find_substring_in_array(row, "saldo iniziale")!=-1 or find_substring_in_array(row, "saldo precedente")!=-1:
            return table[i:]

     # Return the full table if nothing is found
     return table 

# Delete the headers
def headers_delete(table, header):

    cleaned_table = []
    found_header = False
    
    for row in table:
        if row == header:
            if not found_header:
                found_header = True  # Mark the header as found, but don't add it to cleaned_table
        else:
            cleaned_table.append(row)  # Add all rows, except the header
    
    return cleaned_table

#It returns the table up to the final balance.
def get_table_until_saldo_finale(table):
    for i in range(len(table) - 1, -1, -1):
        if find_substring_in_array(table[i], "saldo fin")!=-1:
            return table[:i+1]
    # Return the full table if "saldo finale" is not found
    return table 

#Delete the rows with the description 'None'
def filter_table_by_descrizione(table, header):
    descrizione_index = find_substring_in_array(header, "descrizione")
    if descrizione_index == -1:
        print("Colonna DESCRIZIONE non trovata")
        return table
    
    filtered_table = [row for row in table if row[descrizione_index] is not None]
    return filtered_table

# Delete the rows
def filter_table_by_header_length(table, header):
    header_length = len(header)
    filtered_table = [row for row in table if len(row) == header_length]
    return filtered_table

# Merge the rows
def fix_line_breaks(table, header):
    # Find indexes for 'data' and 'descrizione' columns
    data_index = find_substring_in_array(header, "data")
    descrizione_index = find_substring_in_array(header, "descrizione")

    new_table = []

     # Copy the first row (header)
    if table:
        new_table.append(table[0])

    # Process rows starting from the second and ending at the penultimate
    for i in range(1, len(table) - 1):
        row = table[i]
        # Get the value of the 'data' column
        data_value = row[data_index]
        
        # If 'data' is empty or None, treat as line break
        if data_value is None or not str(data_value).strip():
            # Merge description with previous row if it exists
            if new_table:
                new_table[-1][descrizione_index] += " " + row[descrizione_index]
            else:
                new_table.append(row)  # Add row as is if no previous row
        else:
            new_table.append(row)  # Add row normally if 'data' is valid
    
    # Copy the last row if the table has more than one row
    if len(table) > 1:
        new_table.append(table[-1])
    
    return new_table

# Rearranges the dataset columns
def columns_switcher(table, header):
    
    # Rearranges the dataset columns so that:
    # Column A: 'data'
    # Column C: 'descrizione'
    # Column F: 'dare/entrate/credito'
    # Column G: 'avere/uscite/debito'
   
    final_header_indexes=[0,2,5,6] # Indexes of the final header
    initial_header_indexes= [] # Indexes of the initial header  

    credit_aliases = ["dare", "entrate", "credito"] # Aliases for the debit column
    debit_aliases = ["avere", "uscite", "debito"] # Aliases for the credit column
    
    # Find the indexes of the columns in the initial header
    initial_header_indexes.append(find_substring_in_array(header, "data"))
    initial_header_indexes.append(find_substring_in_array(header, "descrizione"))
    initial_header_indexes.append(find_any_word_in_array(header, credit_aliases))
    initial_header_indexes.append(find_any_word_in_array(header, debit_aliases))

    # Switch the columns according to the final header
    for i in range(len(initial_header_indexes)):
        if initial_header_indexes[i] != -1:
            table = switch_columns(table, initial_header_indexes[i], final_header_indexes[i]) # Switch the columns
            header = switch_cell(header, initial_header_indexes[i], final_header_indexes[i]) # Switch the header cells

            initial_header_indexes = swap_elements(initial_header_indexes, initial_header_indexes[i], final_header_indexes[i])



    # Transform the credit column to numbers
    if(initial_header_indexes[2]!=-1):
        table=transform_column_to_numbers(table, final_header_indexes[2])

    # Transform the debit column to numbers
    if(initial_header_indexes[3]!=-1):
        table=transform_column_to_numbers(table, final_header_indexes[3])

    return table, header

# Check if the sum of incomes and expenses is equal to the final balance
def check_table(table):

    credit_column_number = 5
    debit_column_number = 6

    credit_sum = 0
    debit_sum = 0

    try:
        # Iterate up to the second-to-last row
        for row in table[:-1]:


            credit_value = row[credit_column_number]
            debit_value = row[debit_column_number]
            
             # Treat empty strings as None
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
    
    # Get the final balance from the last row of the table
    if saldo_finale_calculated > 0:
        saldo_finale_exported_table = table[-1][credit_column_number]
    else:
        saldo_finale_exported_table = table[-1][debit_column_number]

    # Round the sums to 2 decimal places and convert to positive values
    saldo_finale_calculated = round(saldo_finale_calculated, 2)
    saldo_finale_calculated = abs(saldo_finale_calculated)    
    

    if(saldo_finale_calculated == saldo_finale_exported_table):
        print("La tabella e' stata esportata correttamente")
    else:
        print("\n\tERRORE: la tabella NON e' stata esportata correttamente")






    


