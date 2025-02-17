# Export the PDF file to an XLSX to be arranged
#from asyncio.windows_events import NULL
import sys
import pandas as pd
from generalFunctions import find_substring_in_array, max_row_length, words_counter, pdf_reader
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
        
        df = pd.DataFrame(data, columns=header)
    
    else:
        df=pd.DataFrame(data, columns=max_row_length(data))

    # Save the DataFrame to an Excel file
    df.to_excel(output1_excel_path, index=False)
    print(f"File Excel salvato in: {output1_excel_path}")

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
        if find_substring_in_array(row, "saldo iniziale")!=-1 or        find_substring_in_array(row, "saldo precedente")!=-1:
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
    
    for i, row in enumerate(table):
        # Get the value of the 'data' column
        data_value = row[data_index]
        
        # If 'data' is empty or None, treat as line break
        if (data_value is None or not str(data_value).strip()) and i < len(table) - 1:
            # Merge description with previous row if it exists
            if new_table:
                new_table[-1][descrizione_index] += " " + row[descrizione_index]
            else:
                new_table.append(row)  # Add row as is if no previous row
        else:
            new_table.append(row)  # Add row normally if 'data' is valid
    
    return new_table

