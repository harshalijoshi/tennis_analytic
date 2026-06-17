import requests
import pandas as pd
import os

DATA_DIR = "data"
API_KEY = "XcrMVIAR3VmmL2ZjyN6Q0haNaX5GOxAu09xSvUsI"  # your SportRadar tennis API key

def collect_data(endpoint: str, filename: str, key_name: str) -> pd.DataFrame:
    """
    General function to fetch data from SportRadar Tennis API and save to CSV.

    Parameters:
    - endpoint: API endpoint (e.g., 'complexes', 'competitions', 'double_competitors_rankings')
    - filename: name of CSV file to save (e.g., 'complexes.csv')
    - key_name: JSON key to normalize (e.g., 'complexes', 'competitions')
    """
    url = f"https://api.sportradar.com/tennis/trial/v3/en/{endpoint}.json?api_key={API_KEY}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # Special handling for doubles competitor rankings
        if endpoint == "double_competitors_rankings":
            # Flatten nested competitor fields inside rankings
            df = pd.json_normalize(
                data.get("rankings", []),
                record_path=None,
                meta=[
                    "rank",
                    "movement",
                    "points",
                    "competitions_played",
                    ["competitor", "id"],
                    ["competitor", "name"],
                    ["competitor", "country"],
                    ["competitor", "country_code"],
                    ["competitor", "abbreviation"],
                ],
                errors="ignore"
            )
            # Rename competitor.* fields to match app.py expectations
            df = df.rename(columns={
                "competitor.id": "competitor.id",
                "competitor.name": "competitor.name",
                "competitor.country": "competitor.country",
                "competitor.country_code": "competitor.country_code",
                "competitor.abbreviation": "competitor.abbreviation"
            })
        else:
            df = pd.json_normalize(data.get(key_name, []))

        # Save to data/ folder
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(os.path.join(DATA_DIR, filename), index=False)

        return df
    else:
        print(f"API error {response.status_code}")
        return pd.DataFrame()
