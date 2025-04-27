import pandas as pd
from main_utils import fetch_comtrade_data
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

api_key = os.getenv("API_KEY")

def prepare_hs_codes(dataset):
    """
    Extracts unique 6-digit HS codes from a CSV dataset of 8- or 10-digit HS codes.

    Args:
        dataset (str): Name of the CSV file (without extension) in the 'data/' directory.

    Returns:
        list: Sorted list of unique 6-digit HS codes as integers.
    """
    df = pd.read_csv("data/raw/" + dataset + ".csv")
    hs_codes = [int(str(num)[:6]) for num in df["8- or 10-Digit HS Code"]]
    return sorted(set(hs_codes))  # Convert to sorted list to preserve order

def get_labels(hs_codes):
    """
    Fetches commodity descriptions from the UN Comtrade API for a list of HS codes.

    Args:
        hs_codes (list): List of 6-digit HS codes.

    Returns:
        list: List of commodity descriptions corresponding to each HS code.
    """
    labels = []
    for i,code in enumerate(hs_codes):
        params = {
            "reporterCode": "",
            "period": 2022,
            "flowCode": "M",
            "cmdCode": code,
            "freq": "A",
            "breakdownMode": "classic",
            "includeDesc": True
        }
        data = fetch_comtrade_data(params, api_key)
        if data:
            labels.append(data[0].get("cmdDesc"))
    return labels

def prepare_commodities(dataset):
    """
    Combines HS codes and their descriptions into a single DataFrame and exports it as a CSV.

    The output is used to power the dropdown menus in the dashboard UI.

    Args:
        dataset (str): Name of the original dataset CSV (without extension) located in 'data/'.

    Raises:
        ValueError: If there is a mismatch between the number of HS codes and their labels.
    """
    hs_codes = prepare_hs_codes(dataset)
    labels = get_labels(hs_codes)
    
    min_len = min(len(labels), len(hs_codes))
    commodity_df = pd.DataFrame({
        "label": labels[:min_len],
        "value": hs_codes[:min_len]
    })
    commodity_df.to_csv("data/" + dataset + "_labels.csv", index=False)

def load_countries():
    """
    Fetches and stores a list of trade partner countries from the UN Comtrade API.

    The function queries total imports for a generic commodity to derive all possible
    partner countries, and stores them as a formatted CSV in the 'data/' folder.

    Output:
        - 'data/countries.csv': A CSV file with dropdown-friendly country names and codes.
    """
    params = {
        "reporterCode": "",
        "period": 2022,
        "flowCode": "M",
        "cmdCode": "TOTAL",
        "freq": "A",
        "breakdownMode": "classic",
        "includeDesc": True
    }
    data = fetch_comtrade_data(params, api_key)
    partners = sorted(list({
        rec["partnerCode"]: rec["partnerDesc"]
        for rec in data if rec.get("partnerCode") and rec.get("partnerDesc")
    }.items()), key=lambda x: x[1])
    countries_list = [{"label": f"{name} ({code})", "value": str(code)} for code, name in partners]
    countries_df = pd.DataFrame(countries_list)
    countries_df.to_csv("data/countries.csv", index=False)  

# Uncomment the following line to load the commodities. Replace "your_dataset_name" with the name of your csv file. 
# Note: This may take a while
# prepare_commodities("your_dataset_name")

# Uncomment the following line to reload the list of countries
# load_countries()
