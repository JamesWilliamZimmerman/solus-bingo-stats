import sqlite3

def main() -> None:
    conn = sqlite3.connect('solus_bingo.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM skilling where player_id=1 ')
    existing_players = cursor.fetchall()

    print(existing_players)
    print('stop')

if __name__ == '__main__':
    main()
