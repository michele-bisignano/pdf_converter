"""
Post-processing for Mistral OCR fallback output.

Applies the same cleaning logic used by the deterministic pipeline
(classify tables, fix line breaks, normalize amounts, extract riepilogo)
but works on DataFrames produced by pd.read_html.
"""

import re
import pandas as pd
from io import StringIO

CORE_COLUMNS = ['Data Operazione', 'Data Valuta', 'Descrizione', 'Addebiti', 'Accrediti']

RIEPILOGO_KEYWORDS = [
    'saldo iniziale', 'saldo precedente',
    'totale accrediti', 'totale addebiti',
    'saldo del periodo', 'saldo finale',
    'totali',
]


def is_transaction_table(html: str) -> bool:
    """Return True when the HTML table contains the 3 transaction markers in any <th>."""
    th_text = re.findall(r'<th[^>]*>(.*?)</th>', html, re.DOTALL | re.IGNORECASE)
    if th_text:
        text = ' '.join(th_text).lower()
    else:
        match = re.search(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        if not match:
            return False
        text = match.group(1).lower()

    has_data = 'data operazione' in text or 'data op.' in text
    has_desc = 'descrizione' in text
    has_import = 'addebiti' in text or 'accrediti' in text
    return has_data and has_desc and has_import


def _find_amount_col(df: pd.DataFrame):
    """Find the single column that contains both addebiti and accrediti keywords."""
    for c in df.columns:
        low = str(c).lower()
        if 'addebiti' in low and 'accrediti' in low:
            return c
    return None


CREDIT_STARTS = ['accredito', 'versam.', 'sconto']
DEBIT_STARTS = ['* pagamento', '* commissioni', '* canone', '* spese',
                'bonifico', 'imposta', '* competenze', '* addebito']


def _is_credit(desc: str) -> bool:
    """Determine if a description indicates a credit transaction."""
    lower = desc.lower().strip()
    for kw in CREDIT_STARTS:
        if lower.startswith(kw):
            return True
    for kw in DEBIT_STARTS:
        if lower.startswith(kw):
            return False
    return False  # default: debit (conservative)


def parse_html_table(html: str) -> pd.DataFrame:
    """Parse a single HTML table string into a DataFrame with flat column names."""
    dfs = pd.read_html(StringIO(html), flavor="lxml")
    if not dfs:
        return None
    df = dfs[0]

    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for c in df.columns:
            if isinstance(c, tuple):
                last = c[-1]
                if isinstance(last, str) and last.startswith('Unnamed'):
                    new_cols.append(c[-2] if len(c) > 1 else last)
                else:
                    new_cols.append(last)
            else:
                new_cols.append(c)
        df.columns = new_cols

    df.columns = [str(c).strip() for c in df.columns]
    return df


def select_core_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the 5 transaction columns.

    Also handles tables where Addebiti and Accrediti are merged into
    a single "Addebiti Accrediti" column by splitting it using the
    description-based heuristics in _is_credit().
    """
    available = [c for c in CORE_COLUMNS if c in df.columns]
    if len(available) == len(CORE_COLUMNS):
        return df[available]

    # Check for a combined "Addebiti Accrediti" column
    merged = _find_amount_col(df)
    if merged and 'Descrizione' in df.columns:
        addebiti = []
        accrediti = []
        for _, row in df.iterrows():
            val = row.get(merged)
            if pd.isna(val) or val is None or str(val).strip() == '':
                addebiti.append(None)
                accrediti.append(None)
            elif _is_credit(str(row.get('Descrizione', ''))):
                addebiti.append(None)
                accrediti.append(val)
            else:
                addebiti.append(val)
                accrediti.append(None)

        result = pd.DataFrame()
        for c in CORE_COLUMNS:
            if c == 'Addebiti':
                result[c] = addebiti
            elif c == 'Accrediti':
                result[c] = accrediti
            elif c in df.columns:
                result[c] = df[c]
        return result

    return df


def drop_header_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where every cell equals the column name (repeated headers)."""
    mask = pd.Series(True, index=df.index)
    for col in df.columns:
        mask &= (df[col].astype(str).str.strip() != str(col).strip())
    return df[mask].copy()


def fix_line_breaks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge split descriptions: when 'Data Operazione' is empty the current row
    is a continuation of the previous row's description.
    """
    if 'Data Operazione' not in df.columns or 'Descrizione' not in df.columns:
        return df

    result = []
    for _, row in df.iterrows():
        data_val = row['Data Operazione']
        is_continuation = pd.isna(data_val) or str(data_val).strip() == ''

        if is_continuation and result:
            prev_desc = str(result[-1]['Descrizione']) if pd.notna(result[-1]['Descrizione']) else ''
            curr_desc = str(row['Descrizione']) if pd.notna(row['Descrizione']) else ''
            result[-1]['Descrizione'] = (prev_desc + ' ' + curr_desc).strip()
        else:
            result.append(row.to_dict())

    return pd.DataFrame(result)


def normalize_amount(value):
    """
    Convert an amount to a float in euro.

    Handles:
    - Italian decimal format  (1.082,10 -> 1082.10)
    - Cent-based integers     (250 -> 2.50, 5110 -> 51.10)
    - Leading-zero strings    ('080' -> 0.80)
    - Already numeric values  (300 -> 3.0)
    - Trailing junk chars     ('+240.434,08 \xa0' -> 240434.08)
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return round(value / 100, 2)

    s = str(value).strip()
    if not s:
        return None

    # Strip trailing non-numeric junk (euro sign, encoding artifacts, etc.)
    s = re.sub(r'[^\d,\-+.]*$', '', s)
    s = s.replace(' ', '')

    is_negative = s.startswith('-')
    if is_negative:
        s = s[1:]

    # Strip leading + sign if present
    s = s.lstrip('+')

    had_comma = ',' in s
    s = s.replace('.', '').replace(',', '.')
    try:
        # Extract first valid number from the cleaned string
        match = re.search(r'-?\d+(\.\d+)?', s)
        num = float(match.group()) if match else None
        if num is None:
            return None
    except (ValueError, AttributeError):
        return None

    if not had_comma:
        num = num / 100

    if is_negative:
        num *= -1
    return round(num, 2)


def normalize_amounts_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply normalize_amount to Addebiti and Accrediti columns."""
    for col in ['Addebiti', 'Accrediti']:
        if col in df.columns:
            df[col] = df[col].apply(normalize_amount)
    return df


def extract_riepilogo_rows(df: pd.DataFrame) -> tuple:
    """
    Split a DataFrame into (riepilogo_df, movements_df).

    Riepilogo rows are those whose Descrizione contains a summary keyword.
    """
    if 'Descrizione' not in df.columns:
        return pd.DataFrame(), df

    mask = pd.Series(False, index=df.index)
    for kw in RIEPILOGO_KEYWORDS:
        mask |= df['Descrizione'].astype(str).str.lower().str.contains(kw, na=False)

    riepilogo = df[mask].copy()
    movements = df[~mask].copy()
    return riepilogo, movements


def extract_riepilogo_simple(html: str) -> dict:
    """Parse a simple 2-column riepilogo table and return {label: amount}.

    Only processes tables with exactly 2 columns (label | amount pattern).
    Ignores wider transaction-style tables.
    """
    df = parse_html_table(html)
    # Only handle true 2-column riepilogo tables
    if df is None or df.shape[1] != 2:
        return {}
    result = {}
    for _, row in df.iterrows():
        label = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ''
        raw = row.iloc[1]
        if 'saldo iniziale' in label:
            result['saldo_iniziale'] = normalize_amount(raw)
        elif 'saldo finale' in label:
            result['saldo_finale'] = normalize_amount(raw)
        elif 'totale accrediti' in label:
            result['totale_accrediti'] = normalize_amount(raw)
        elif 'totale addebiti' in label:
            result['totale_addebiti'] = normalize_amount(raw)
    return result


def df_to_export_format(df: pd.DataFrame) -> pd.DataFrame:
    """Final clean-up before writing to Excel: reset index, drop all-NaN rows."""
    df = df.dropna(how='all').reset_index(drop=True)
    df = df.dropna(axis=1, how='all')
    return df
