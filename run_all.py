import publish_stats
import publish_bosses
import publish_skills
import publish_clues
import publish_bingo_exp
import fetch_stats
import fetch_roster
import asyncio

async def main() -> None:
    await fetch_roster.main()
    await fetch_stats.main()
    publish_bosses.main()
    publish_skills.main()
    publish_clues.main()
    publish_stats.main()
    publish_bingo_exp.main()

if __name__ == '__main__':
    asyncio.run(main())
