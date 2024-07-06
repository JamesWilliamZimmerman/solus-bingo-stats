import sqlite3
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime

def main() -> None:
    conn = sqlite3.connect('solus_bingo.db')

    query = '''
    SELECT
        p.rsn,
        p.team,
        c.clue_type,
        c.clue_completions,
        c.created_date
    FROM clues c
    JOIN players p
    ON c.player_id = p.id
    ORDER BY p.team, p.rsn, c.clue_type, c.created_date
    '''

    df = pd.read_sql_query(query, conn)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values(by=['team', 'rsn', 'clue_type', 'created_date'])
    df['delta_clue_completions'] = df.groupby(['rsn', 'clue_type'])['clue_completions'].diff().fillna(0)
    df['cumulative_clue_completions'] = df.groupby(['rsn', 'clue_type'])['delta_clue_completions'].cumsum()

    most_recent_df = df.groupby(['rsn', 'clue_type']).tail(1)

    most_recent_df['created_date'] = most_recent_df['created_date'].astype(str)

    pivot_df = most_recent_df.pivot(index=['rsn', 'team'], columns='clue_type', values=['clue_completions', 'delta_clue_completions', 'cumulative_clue_completions', 'created_date'])

    pivot_df.columns = ['_'.join(col).strip() for col in pivot_df.columns.values]
    pivot_df.reset_index(inplace=True)

    columns_order = ['rsn', 'team']
    for clue_type in df['clue_type'].unique():
        columns_order.extend([
            f'clue_completions_{clue_type}',
            f'delta_clue_completions_{clue_type}',
            f'cumulative_clue_completions_{clue_type}',
            f'created_date_{clue_type}'
        ])
    clues_df = pivot_df[columns_order]

    SERVICE_ACCOUNT_FILE = 'solus-bingo-b27ae970a08f.json'

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    SPREADSHEET_ID = '1i7OSaNlZIUyLtgLmXV4F9S-UIYhMWg8DLRb11BbAX-U'

    sheet_title = f"Clues Report"

    service = build('sheets', 'v4', credentials=credentials)

    requests = [{
        'addSheet': {
            'properties': {
                'title': sheet_title
            }
        }
    }]
    body = {
        'requests': requests
    }
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
    except HttpError:
        response = None
        print('sheet exists')

    num_rows = clues_df.shape[0] + 1  
    num_rows = 2100

    range_end = f"ZZZ{num_rows}"
    range_name = f"{sheet_title}!A1:{range_end}"

    values = [clues_df.columns.tolist()] + clues_df.values.tolist()

    body = {
        'values': values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    if response != None:
        column_width_request = {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': response['replies'][0]['addSheet']['properties']['sheetId'],
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(clues_df.columns)  
                },
                'properties': {
                    'pixelSize': 200  
                },
                'fields': 'pixelSize'
            }
        }
        
        body = {
            'requests': [column_width_request]
        }
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

    efficiency_sheet_title = "Efficiency"
    ehc_range_start = 'E2'
    clue_ehc_values_start = 'I4'
    letters = []
    for index, column in enumerate(clues_df.columns.tolist()):
        if 'cumulative_clue_completions' in column:
            if 'All' not in column and 'Beginner' not in column:
                letters.append(col_num_to_letter(index + 1))  

    formulas = []
    for i in range(2, len(clues_df) + 2):  
        formula = "=SUM("
        parts = []
        for j, letter in enumerate(letters):
            parts.append(f"('{sheet_title}'!{letter}{i}/{clue_ehc_values_start[0]}{j+4})")  
        formula += ",".join(parts) + ")"
        formulas.append(formula)

    efficiency_values = [[formulas[i - 2]] for i in range(2, len(clues_df) + 2)]
    efficiency_range = f"{efficiency_sheet_title}!{ehc_range_start}:{ehc_range_start[0]}{len(efficiency_values) + 1}"

    body = {
        'values': efficiency_values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=efficiency_range,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    conn.close()

    print(f"{result.get('updatedCells')} cells updated.")
    print('done with clues report')

def col_num_to_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

if __name__ == '__main__':
    main()

