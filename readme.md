# Scripts to run stats for Solus bingo events

## Requirements:
- Linux OS 
- Python 3.12
- Pipenv
- Google Service account

## How to run:
- Clone to local machine
- Run ```pipenv install```
- Update references to Google service:
    - Service account credential file
    - Google sheet
        - Example sheet included
        - May require updates for EHX values
- Update WOM competition ID 
    - Optionally create WOM api key
    - Run ```export WOM_API_KEY=XXXXXXXXXX```
    - Run ```export USER_AGENT=discord_username```
- Run ```pipenv shell```
- Run ```python run_all.py```

Happy bingo!

