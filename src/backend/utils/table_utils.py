def find_substring_in_array(array, search_string):
    search_string = search_string.lower()
    for index, element in enumerate(array):
        if element and search_string in element.lower():
            return index
    return -1


def find_any_word_in_array(array, search_string_array):
    for word in search_string_array:
        idx = find_substring_in_array(array, word)
        if idx != -1:
            return idx
    return -1


def max_row_length(table):
    max_len = max(len(row) for row in table)
    return [str(i) for i in range(max_len)]


def words_counter(text):
    return len(text.split())


def switch_cell(array, cell1, cell2):
    if cell1 == cell2:
        return array
    max_index = max(cell1, cell2)
    if max_index >= len(array):
        array.extend([None] * (max_index + 1 - len(array)))
    array[cell1], array[cell2] = array[cell2], array[cell1]
    return array


def swap_elements(array, element1, element2):
    if element1 in array and element2 in array:
        index1 = array.index(element1)
        index2 = array.index(element2)
        if index2 > index1:
            array = switch_cell(array, index1, index2)
    return array


def transform_column_to_numbers(table, column_number):
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
    column_data = []
    for row in table:
        if col_index < len(row):
            column_data.append(row[col_index])
        else:
            column_data.append('')
    return column_data


def column_writer(table, col_index, data_column, start_row=0):
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
