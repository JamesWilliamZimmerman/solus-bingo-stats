import sqlite3
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

def main() -> None:
    conn = sqlite3.connect('solus_bingo.db')

    query = '''
    SELECT
        p.rsn,
        p.team,
        s.skill_name,
        s.exp,
        s.ehp,
        s.created_date
    FROM skilling s
    JOIN players p
    ON s.player_id = p.id
    ORDER BY p.team, p.rsn, s.skill_name, s.created_date
    '''

    df = pd.read_sql_query(query, conn)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values(by=['team', 'rsn', 'skill_name', 'created_date'])
    df['delta_exp'] = df.groupby(['rsn', 'skill_name'])['exp'].diff().fillna(0)
    df['delta_ehp'] = df.groupby(['rsn', 'skill_name'])['ehp'].diff().fillna(0)
    df['cumulative_exp'] = df.groupby(['rsn', 'skill_name'])['delta_exp'].cumsum()
    df['cumulative_ehp'] = df.groupby(['rsn', 'skill_name'])['delta_ehp'].cumsum()

    most_recent_df = df.groupby(['rsn', 'skill_name']).tail(1)

    most_recent_df['created_date'] = most_recent_df['created_date'].astype(str)

    pivot_df = most_recent_df.pivot(index=['rsn', 'team'], columns='skill_name', values=['exp', 'delta_exp', 'cumulative_exp', 'ehp', 'delta_ehp', 'cumulative_ehp', 'created_date'])

    pivot_df.columns = ['_'.join(col).strip() for col in pivot_df.columns.values]
    pivot_df.reset_index(inplace=True)

    columns_order = ['rsn', 'team']
    for skill in df['skill_name'].unique():
        columns_order.extend([
            f'exp_{skill}',
            f'delta_exp_{skill}',
            f'cumulative_exp_{skill}',
            f'ehp_{skill}',
            f'delta_ehp_{skill}',
            f'cumulative_ehp_{skill}',
            f'created_date_{skill}'
        ])
    skilling_df = pivot_df[columns_order]

    SERVICE_ACCOUNT_FILE = 'solus-bingo-b27ae970a08f.json'

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    SPREADSHEET_ID = '1i7OSaNlZIUyLtgLmXV4F9S-UIYhMWg8DLRb11BbAX-U'

    sheet_title = f"Skilling Report"

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
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()

    num_rows = skilling_df.shape[0] + 1  
    num_rows = 2100

    range_end = f"ZZZ{num_rows}"
    range_name = f"{sheet_title}!A1:{range_end}"

    values = [skilling_df.columns.tolist()] + skilling_df.values.tolist()

    body = {
        'values': values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    column_width_request = {
        'updateDimensionProperties': {
            'range': {
                'sheetId': response['replies'][0]['addSheet']['properties']['sheetId'],
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': len(skilling_df.columns)  
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
    ehp_range_start = 'D2'
    skill_ehp_values_start = 'O3'
    letters = []
    for index, column in enumerate(skilling_df.columns.tolist()):
        if 'cumulative_exp' in column:
            if 'Overall' not in column and 'Hitpoints' not in column and 'Magic' not in column:
                letters.append(col_num_to_letter(index + 1))  

    formulas = []
    for i in range(2, len(skilling_df) + 2):  
        formula = "=SUM("
        parts = []
        for j, letter in enumerate(letters):
            parts.append(f"('{sheet_title}'!{letter}{i}/{skill_ehp_values_start[0]}{j+3})")  
        formula += ",".join(parts) + ")"
        formulas.append(formula)

    efficiency_values = [[formulas[i - 2]] for i in range(2, len(skilling_df) + 2)]
    efficiency_range = f"{efficiency_sheet_title}!{ehp_range_start}:{ehp_range_start[0]}{len(efficiency_values) + 1}"

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

    print(f"{result.get('updatedCells')} cells updated.")
    print('done with skilling report')

if __name__ == '__main__':
    main()

