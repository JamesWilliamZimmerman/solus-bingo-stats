import sqlite3
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest
import datetime

def main() -> None:
    conn = sqlite3.connect('solus_bingo.db')

    query = '''
    SELECT
        p.rsn,
        p.team,
        b.boss_name,
        b.kills,
        b.ehb,
        b.created_date
    FROM bossing b
    JOIN players p
    ON b.player_id = p.id
    ORDER BY p.team, p.rsn, b.boss_name, b.created_date
    '''

    df = pd.read_sql_query(query, conn)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values(by=['team', 'rsn', 'boss_name', 'created_date'])
    df['delta_kills'] = df.groupby(['rsn', 'boss_name'])['kills'].diff().fillna(0)
    df['delta_ehb'] = df.groupby(['rsn', 'boss_name'])['ehb'].diff().fillna(0)
    df['cumulative_kills'] = df.groupby(['rsn', 'boss_name'])['delta_kills'].cumsum()
    df['cumulative_ehb'] = df.groupby(['rsn', 'boss_name'])['delta_ehb'].cumsum()

    most_recent_df = df.groupby(['rsn', 'boss_name']).tail(1)

    most_recent_df['created_date'] = most_recent_df['created_date'].astype(str)

    pivot_df = most_recent_df.pivot(index=['rsn', 'team'], columns='boss_name', values=['kills', 'delta_kills', 'cumulative_kills', 'ehb', 'delta_ehb', 'cumulative_ehb', 'created_date'])

    pivot_df.columns = ['_'.join(col).strip() for col in pivot_df.columns.values]
    pivot_df.reset_index(inplace=True)

    columns_order = ['rsn', 'team']
    for boss in df['boss_name'].unique():
        columns_order.extend([
            f'kills_{boss}',
            f'delta_kills_{boss}',
            f'cumulative_kills_{boss}',
            f'ehb_{boss}',
            f'delta_ehb_{boss}',
            f'cumulative_ehb_{boss}',
            f'created_date_{boss}'
        ])
    bossing_df = pivot_df[columns_order]

    SERVICE_ACCOUNT_FILE = 'solus-bingo-b27ae970a08f.json'

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    SPREADSHEET_ID = '1i7OSaNlZIUyLtgLmXV4F9S-UIYhMWg8DLRb11BbAX-U'

    sheet_title = f"Bossing Report"

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

    num_rows = bossing_df.shape[0] + 1  
    num_rows = 2100

    range_end = f"ZZZ{num_rows}"
    range_name = f"{sheet_title}!A1:{range_end}"

    values = [bossing_df.columns.tolist()] + bossing_df.values.tolist()

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
                    'endIndex': len(bossing_df.columns)  
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
        ehb_range_start = 'C2'
        boss_ehb_values_start = 'L3'
        letters = []
        for index, column in enumerate(bossing_df.columns.tolist()):
            if 'cumulative_kills' in column:
                if 'Tempoross' not in column and 'Wintertodt' not in column and 'Zalcano' not in column and 'Guardians Of The Rift' not in column:
                    letters.append(col_num_to_letter(index + 1))  

        formulas = []
        for i in range(2, len(bossing_df) + 2):  
            formula = "=SUM("
            parts = []
            for j, letter in enumerate(letters):
                parts.append(f"('{sheet_title}'!{letter}{i}/{boss_ehb_values_start[0]}{j+3})")  
            formula += ",".join(parts) + ")"
            formulas.append(formula)

        efficiency_values = [[formulas[i - 2]] for i in range(2, len(bossing_df) + 2)]
        efficiency_range = f"{efficiency_sheet_title}!{ehb_range_start}:{ehb_range_start[0]}{len(efficiency_values) + 1}"

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
    print('done with bossing report')

def col_num_to_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

if __name__ == '__main__':
    main()

