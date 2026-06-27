from src.backend.utils.table_utils import find_substring_in_array, find_any_word_in_array, switch_columns, switch_cell, swap_elements, transform_column_to_numbers


def is_table_empty(table):
    if not table:
        return True
    for row in table:
        if row:
            return False
    return True


def find_row_with_data_and_descrizione(table):
    for row in table:
        if find_substring_in_array(row, "data") != -1 and find_substring_in_array(row, "descrizione") != -1:
            return row
    print("\n\tWARNING: header not found\n")
    return []


def copy_table_from_saldo_iniziale(table):
    for i, row in enumerate(table):
        if find_substring_in_array(row, "saldo iniziale") != -1 or find_substring_in_array(row, "saldo precedente") != -1:
            return table[i:]
    return table


def headers_delete(table, header):
    return [row for row in table if not (find_substring_in_array(row, "descrizione") != -1 and find_substring_in_array(row, "data") != -1)]


def get_table_until_saldo_finale(table):
    for i in range(len(table) - 1, -1, -1):
        if find_substring_in_array(table[i], "saldo fin") != -1:
            return table[:i + 1]
    return table


def filter_table_by_descrizione(table, header):
    descrizione_index = find_substring_in_array(header, "descrizione")
    if descrizione_index == -1:
        print("DESCRIPTION column not found")
        return table
    return [row for row in table if row[descrizione_index] is not None]


def filter_table_by_header_length(table, header):
    header_length = len(header)
    result = []
    for row in table:
        if len(row) == header_length:
            result.append(row)
        elif len(row) < header_length:
            # Pad short rows (e.g. saldo rows) to match header length
            result.append(row + [''] * (header_length - len(row)))
        # Drop rows longer than header (malformed)
    return result


def fix_line_breaks(table, header):
    data_index = find_substring_in_array(header, "data")
    descrizione_index = find_substring_in_array(header, "descrizione")

    if data_index == -1 or descrizione_index == -1:
        print("WARNING: data or descrizione column not found -- skipping fix_line_breaks")
        return table

    new_table = []
    if table:
        new_table.append(table[0])

    for i in range(1, len(table) - 1):
        row = table[i]
        data_value = row[data_index] if data_index < len(row) else None
        if data_value is None or not str(data_value).strip():
            if new_table:
                curr = row[descrizione_index] if descrizione_index < len(row) else None
                prev = new_table[-1][descrizione_index] if descrizione_index < len(new_table[-1]) else None
                new_table[-1][descrizione_index] = (prev or "") + " " + (curr or "")
            else:
                new_table.append(row)
        else:
            new_table.append(row)

    if len(table) > 1:
        new_table.append(table[-1])

    return new_table


def columns_switcher(table, header):
    final_header_indexes = [0, 2, 5, 6]
    initial_header_indexes = []

    credit_aliases = ["avere", "entrate", "credito"]   # "avere" = crediti/entrate
    debit_aliases = ["dare", "uscite", "debito"]        # "dare" = debiti/uscite

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
