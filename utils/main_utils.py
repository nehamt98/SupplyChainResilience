import requests
import time
import pandas as pd

def fetch_comtrade_data(params, api_key, retries=3):
    """
    Fetches trade data from the UN Comtrade API based on specified parameters.

    Args:
        params (dict): Query parameters for the API call, including reporterCode, flowCode, cmdCode, etc.
        api_key (str): User's API key for authorization.
        retries (int): Number of retry attempts if rate-limited or request fails (default is 3).

    Returns:
        list: List of trade records (dictionaries), or empty list if request fails or data not found.
    """
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
    """
    Validates if a given trade partner is meaningful for analysis.

    Args:
        partner (str): Name of the trade partner country or region.

    Returns:
        bool: True if partner is valid , False otherwise.
    """
    if not partner:
        return False
    partner = partner.lower()
    return not any(x in partner for x in ["world"])

def fetch_countries():
    """
    Loads the list of countries available for selection in the dashboard.

    Returns:
        list: List of dictionaries with 'label' and 'value' keys used for Dash dropdowns.
    """
    countries_df = pd.read_csv("data/countries.csv")
    return countries_df.to_dict(orient="records")   

def fetch_commodities():
    """
    Loads the list of critical commodities (with HS codes and labels) from preprocessed CSV.

    Returns:
        list: List of dictionaries with 'label' and 'value' keys used for Dash dropdowns.
    """
    # Replace file name with your prepared csv
    commodities_df = pd.read_csv("data/semiconductors_labels.csv")    
    return commodities_df.to_dict(orient="records")

# To store cached data
trade_data_cache = {}

def get_trade_partners(country, flow, hs_code, year, api_key):
    """
    Retrieves trade partner values for a given country, commodity, year, and trade flow type.

    Uses in-memory caching to avoid repeated API calls for the same query.

    Args:
        country (str): UN Comtrade reporter country code.
        flow (str): 'M' for imports or 'X' for exports.
        hs_code (str or int): Harmonized System commodity code (6-digit).
        year (int): Year of trade data.
        api_key (str): User's API key for the UN Comtrade API.

    Returns:
        dict: Dictionary mapping partner countries to trade values (USD).
    """
    cache_key = (country, year, hs_code, flow)
    if cache_key in trade_data_cache:
        return trade_data_cache[cache_key]
    
    params = {
        "reporterCode": country,
        "period": year,
        "flowCode": flow,
        "cmdCode": hs_code,
        "freq": "A",
        "breakdownMode": "classic",
        "includeDesc": True
    }
    data = fetch_comtrade_data(params, api_key)
    partner_values = {}
    for rec in data:
        partner = rec.get("partnerDesc")
        value = rec.get("primaryValue")
        if is_valid_partner(partner) and value:
            try:
                val = float(value)
                if val > 0:
                    partner_values[partner] = partner_values.get(partner, 0) + val
            except ValueError:
                continue
    
    trade_data_cache[cache_key] = partner_values
    return partner_values

def calculate_scri(imports, exports):
    """
    Calculates the Supply Chain Resilience Index (SCRI) for a commodity.

    Args:
        imports (dict): Dictionary of import values by partner country.
        exports (dict): Dictionary of export values by partner country.

    Returns:
        dict: A dictionary containing:
            - Total Imports (USD)
            - Total Exports (USD)
            - HHI (float)
            - Diversity Score (float)
            - IDI (float)
            - SCRI (float)
            - Import Partners (int)
    """
    M = sum(imports.values())
    X = sum(exports.values())
    N = len(imports)
    HHI = sum((v / M) ** 2 for v in imports.values()) if M > 0 else 0.0
    DiversityScore = min(N / 193.0, 1.0)
    IDI = max(min((M - X) / M, 1.0), 0.0) if M > 0 else 0.0
    SCRI = round(HHI * (1 - DiversityScore) * IDI, 4)
    return {
        "Total Imports": M,
        "Total Exports": X,
        "HHI": round(HHI, 4),
        "Diversity Score": round(DiversityScore, 4),
        "IDI": round(IDI, 4),
        "SCRI": SCRI,
        "Import Partners": N
    }