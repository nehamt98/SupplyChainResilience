import pandas as pd
from main_utils import fetch_comtrade_data
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

api_key = os.getenv("API_KEY")

# Get unique 6-digit HS codes
def prepare_hs_codes(dataset):
    df = pd.read_csv("data/" + dataset + ".csv")
    hs_codes = [int(str(num)[:6]) for num in df["8- or 10-Digit HS Code"]]
    return sorted(set(hs_codes))  # Convert to sorted list to preserve order

# Get descriptions for each HS code
def get_labels(hs_codes):
    labels = []
    for code in hs_codes:
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
        labels.append(data[0].get("cmdDesc"))
    return labels

# Combine labels and values into a DataFrame
def prepare_commodities(dataset):
    hs_codes = prepare_hs_codes(dataset)
    labels = get_labels(hs_codes)
    
    # Ensure both lists are the same length before combining
    if len(labels) != len(hs_codes):
        raise ValueError("Mismatch between labels and HS codes length.")
    
    commodity_df = pd.DataFrame({
        "label": labels,
        "value": hs_codes
    })

    commodity_df.to_csv("data/" + dataset + "_labels.csv", index=False)

def load_countries():
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

# Enter the name of the csv file to load the labels and values of the commodities
prepare_commodities("semiconductors")
# Load the list of countries
load_countries()