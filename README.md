# SupplyChainResilience
An interactive dashboard tool for visualizing and assessing supply chain vulnerabilities in critical goods for any country and year.
Built using Dash (Plotly) and powered by UN Comtrade trade flow data.

## Features
- Select any country, year, and commodity
- Compute supply chain metrics including:
    - Herfindahl-Hirschman Index (HHI)
    - Diversity Score
    - Import Dependency Index (IDI)
    - SCRI (Composite metric)
- Visual policy recommendations based on SCRI score
- Compare SCRI scores across multiple commodities
- Support for plug-and-play with any CSV of critical goods

## Metrics
The SCRI (Supply Chain Resilience Index) combines three metrics:
- HHI (Herfindahl-Hirschman Index): Measures concentration of import partners
- Diversity Score: Scales from 0 to 1 based on how many partners a country imports from
- Import Dependency Index (IDI): Measures reliance on imports versus exports

SCRI = HHI × (1 - Diversity Score) × IDI

Higher SCRI = higher vulnerability.

## Setup Instructions
1. Clone the repository
```
git clone https://github.com/nehamt98/SupplyChainResilience.git
cd SupplyChainResilience
```
2. Install dependencies
```
pip install -r requirements.txt
```
## Preprocessing Your Own Data
To analyze a new set of critical goods:
1. Replace or add your own CSV in the data/ folder.
The CSV should have a column named: 8- or 10-Digit HS Code. This data will be available in [Criticial Supply Chains](https://www.trade.gov/data-visualization/draft-list-critical-supply-chains)
2. In prepare_data.py, uncomment the line:
prepare_commodities(“your_dataset_name”)
This creates a your_dataset_name_labels.csv file with HS code descriptions.
3. (Optional) Regenerate countries list by uncommenting:
load_countries()
4. Run the script once:
python utils/prepare_data.py
5. In main_utils.py, change the file name in fetch_commodities():
pd.read_csv(“data/your_dataset_name_labels.csv”)

## Running the app
```
python main.py
```
The app runs locally at: http://127.0.0.1:8055/

## How to Use
1. Enter your UN Comtrade API Key
2.	Select a country, year, and commodity
3.	View:
    - Metrics
	- Import distribution pie chart
	- Risk level with policy suggestions
4.	Scroll down to select multiple commodities for comparative SCRI scores

## Policy Recommendations Logic
Based on the SCRI score:
- High Risk (SCRI > 0.5):
	- Strong reliance on few suppliers
	- Suggests diversifying or reducing import dependency
- Medium Risk (0.2 < SCRI ≤ 0.5):
	- Moderately concentrated supply
	- Recommend supplier monitoring and bilateral deals
- Low Risk (SCRI ≤ 0.2):
	- Resilient and well-diversified
	- Continue with current policies and monitor

## Notes
- The app uses in-memory caching for trade data to limit API calls.
- Dropdowns are dynamically generated from preloaded CSVs.
- Detailed explanation of the metrics used - [Vulnerability_Calculation.md](docs/Vulnerability_Calculation.md)
- Correlation analysis of the scores - [scores_correlation.ipynb](notebooks/scores_correlation.ipynb)
