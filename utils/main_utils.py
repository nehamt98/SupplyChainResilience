import requests
import time

# === Helper Functions ===
def fetch_comtrade_data(params, api_key, retries=3):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    for attempt in range(retries):
        try:
            response = requests.get("https://comtradeapi.un.org/data/v1/get/C/A/HS", params=params, headers=headers)
            if response.status_code == 200:
                return response.json().get("data", [])
            elif response.status_code == 429:
                time.sleep(5 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print("Connection error:", e)
    return []

def is_valid_partner(partner):
    if not partner:
        return False
    partner = partner.lower()
    return not any(x in partner for x in ["world"])
