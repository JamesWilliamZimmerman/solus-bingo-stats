import sqlite3

def run() -> None:
    conn = sqlite3.connect('solus_bingo.db')

    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rsn TEXT NOT NULL,
        team TEXT,
        build TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        ehb FLOAT,
        ehp FLOAT,
        ehc FLOAT,
        snapshot_date TIMESTAMP,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skilling (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        exp INTEGER,
        ehp FLOAT,
        rank INTEGER,
        snapshot_date TIMESTAMP,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bossing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        boss_name TEXT NOT NULL,
        kills INTEGER,
        ehb FLOAT,
        rank INTEGER,
        snapshot_date TIMESTAMP,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        clue_type TEXT,
        clue_completions INTEGER,
        rank INTEGER,
        snapshot_date TIMESTAMP,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
    ''')

    conn.commit()
    conn.close()
