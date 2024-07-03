import wom
import asyncio
import make_migrations
import sqlite3
import os

async def main() -> None:
    make_migrations.run()

    WOM_KEY = os.getenv('WOM_API_KEY')
    WOM_AGENT = os.getenv('USER_AGENT')
    client = wom.Client(WOM_KEY, user_agent=WOM_AGENT)
    await client.start()

    conn = sqlite3.connect('solus_bingo.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM players')
    existing_players = {row[1] for row in cursor.fetchall()}

    result = await client.competitions.get_details(id=37530)

    if result.is_ok:
        unwrapped_result = result.unwrap()
    else:
        unwrapped_result = None
        print(result.unwrap_err)

    result_dict = unwrapped_result.to_dict()
    for participant in result_dict['participations']:
        player = participant['participation']['player']
        team = participant['participation']['data']['team_name']
        rsn = player['display_name']
        build = player['build'].name
        if rsn not in existing_players:
            cursor.execute('''
            INSERT INTO players (rsn, team, build)
            VALUES (?, ?, ?)
            ''', (rsn, team, build))

            existing_players.add(rsn)

    conn.commit()

    cursor.execute('SELECT * FROM players')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        print(row)
        count += 1
    print(count)

    await client.close()
    conn.close()

    print('done')


if __name__ == '__main__':
    asyncio.run(main())
