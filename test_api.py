import requests
import pandas as pd

API_KEY = "XcrMVIAR3VmmL2ZjyN6Q0haNaX5GOxAu09xSvUsI"
url = f"https://api.sportradar.com/tennis/trial/v3/en/complexes.json?api_key={API_KEY}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    df = pd.json_normalize(data.get("complexes", []))
    print("✅ API call successful!")
    print(df.head())  # show first 5 rows
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
