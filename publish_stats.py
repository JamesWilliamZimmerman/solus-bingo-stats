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
        s.ehb,
        s.ehp,
        s.ehc,
        s.created_date
    FROM stats s
    JOIN players p
    ON s.player_id = p.id
    ORDER BY p.team, p.rsn, s.created_date DESC
    '''

    df = pd.read_sql_query(query, conn)

    df['created_date'] = pd.to_datetime(df['created_date'])
    df = df.sort_values(by=['team','rsn', 'created_date'])
    df['delta_ehb'] = df.groupby('rsn')['ehb'].diff().fillna(0)
    df['delta_ehp'] = df.groupby('rsn')['ehp'].diff().fillna(0)
    df['delta_ehc'] = df.groupby('rsn')['ehc'].diff().fillna(0)
    df['cumulative_ehb'] = df.groupby('rsn')['delta_ehb'].cumsum()
    df['cumulative_ehp'] = df.groupby('rsn')['delta_ehp'].cumsum()
    df['cumulative_ehc'] = df.groupby('rsn')['delta_ehc'].cumsum()

    most_recent_df = df.groupby('rsn').tail(1)

    stats_df = most_recent_df[['rsn', 'team', 'ehb', 'delta_ehb', 'cumulative_ehb', 'ehp', 'delta_ehp', 'cumulative_ehp', 'ehc', 'delta_ehc', 'cumulative_ehc', 'created_date']]

    stats_df['created_date'] = stats_df['created_date'].astype(str)

    SERVICE_ACCOUNT_FILE = 'solus-bingo-b27ae970a08f.json'

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    SPREADSHEET_ID = '1i7OSaNlZIUyLtgLmXV4F9S-UIYhMWg8DLRb11BbAX-U'

    sheet_title = f"Basic Stats Report"

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

    num_rows = stats_df.shape[0] + 1  
    num_rows = 2100

    range_end = f"ZZ{num_rows}"
    range_name = f"{sheet_title}!A1:{range_end}"

    values = [stats_df.columns.tolist()] + stats_df.values.tolist()

    body = {
        'values': values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    conn.close()

    print(f"{result.get('updatedCells')} cells updated.")
    print('done with base stats')

if __name__ == '__main__':
    main()

