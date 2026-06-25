import pandas as pd


def export_to_excel(data, header, output_path):
    """Write data to Excel and run verification."""
    if header:
        df = pd.DataFrame(data, columns=header)
    else:
        from src.backend.utils.table_utils import max_row_length
        df = pd.DataFrame(data, columns=max_row_length(data))

    df.to_excel(output_path, index=False)
    print(f"File Excel salvato in: {output_path}")
    check_table(data)


def check_table(table):
    """Check if the sum of incomes and expenses equals the final balance."""
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
    except ValueError:
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
