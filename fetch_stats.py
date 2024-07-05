import wom
import asyncio
import time
import sqlite3
import os

async def main() -> None:
    WOM_KEY = os.getenv('WOM_API_KEY')
    WOM_AGENT = os.getenv('USER_AGENT')
    client = wom.Client(WOM_KEY, user_agent=WOM_AGENT)
    await client.start()

    conn = sqlite3.connect('solus_bingo.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM players')
    players = list(row[1] for row in cursor.fetchall())
    cursor.execute('SELECT * FROM players')
    player_dict = {row[1]: row[0] for row in cursor.fetchall()}

    for rsn in players:
        result = await client.players.update_player(username=rsn)
        if result.is_ok:
            pass
        else:
            print(result.unwrap_err)

        result = await client.players.get_details(username=rsn)
        if result.is_ok:
            unwrapped_result = result.unwrap()
        else:
            unwrapped_result = None
            print(result.unwrap_err)

        player_detail = unwrapped_result.to_dict()

        player_id = player_dict[rsn]
        snapshot_date = player_detail['latest_snapshot']['created_at']

        for skill in player_detail['latest_snapshot']['data']['skills'].values():
            metric = skill['metric']
            skill_name = metric.name
            exp = skill['experience']
            ehp = skill['ehp']
            rank = skill['rank']

            cursor.execute('''
            INSERT INTO skilling (player_id, skill_name, exp, ehp, rank, snapshot_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_id, skill_name, exp, ehp, rank, snapshot_date))

        conn.commit()

        for boss in player_detail['latest_snapshot']['data']['bosses'].values():
            metric = boss['metric']
            boss_name = metric.value.replace('_', ' ').title()
            kills = boss['kills']
            ehb = boss['ehb']
            rank = boss['rank']

            cursor.execute('''
            INSERT INTO bossing (player_id, boss_name, kills, ehb, rank, snapshot_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_id, boss_name, kills, ehb, rank, snapshot_date))

        conn.commit()

        for activity in player_detail['latest_snapshot']['data']['activities'].values():
            metric = activity['metric']
            activity_name = metric.value.replace('_', ' ').title()
            if 'Clue' in activity_name:
                clue_completions = activity['score']
                cursor.execute('''
                INSERT INTO clues (player_id, clue_type, clue_completions, rank, snapshot_date)
                VALUES (?, ?, ?, ?, ?)
                ''', (player_id, activity_name, clue_completions, rank, snapshot_date))
            if 'Guardian' in activity_name:
                ehb = 0.0
                kills = activity['score']
                rank = activity['rank']
                cursor.execute('''
                INSERT INTO bossing (player_id, boss_name, kills, ehb, rank, snapshot_date)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (player_id, activity_name, kills, ehb, rank, snapshot_date))

        conn.commit()

        ehb = player_detail['player']['ehb']
        ehp = player_detail['player']['ehp']

        cursor.execute('''
        INSERT INTO stats (player_id, ehb, ehp, snapshot_date)
        VALUES (?, ?, ?, ?)
        ''', (player_id, ehb, ehp, snapshot_date))

        conn.commit()

        time.sleep(3)


    await client.close()


if __name__ == '__main__':
    asyncio.run(main())

