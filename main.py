#!/usr/bin/env python
# coding: utf-8

# In[17]:


# Supply Chain Resilience Explorer Dashboard

# 📦 Required Libraries
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output, no_update
import plotly.express as px
import plotly.graph_objects as go
import time

# Fetch Countries Based on Partner Data
def fetch_countries(api_key):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
    params = {
        "reporterCode": "",  # UK as sample
        "period": 2022,
        "flowCode": "M",
        "cmdCode": "TOTAL",
        "freq": "A",
        "breakdownMode": "classic",
        "includeDesc": True
    }
    try:
        res = requests.get(url, params=params, headers=headers)
        if res.status_code == 200:
            data = res.json().get("data", [])
            partners = sorted(list({
                rec["partnerCode"]: rec["partnerDesc"]
                for rec in data if rec.get("partnerCode") and rec.get("partnerDesc")
            }.items()), key=lambda x: x[1])
            return [{"label": f"{name} ({code})", "value": str(code)} for code, name in partners]
    except Exception as e:
        print("❌ Exception while fetching countries:", e)
    return []

# Static dropdown options
year_options = [{"label": str(y), "value": y} for y in range(2010, 2024)]
commodity_options = [
    {"label": "Semiconductors (8541)", "value": "8541"},
    {"label": "Vaccines (3002)", "value": "3002"},
    {"label": "Lithium Batteries (8507)", "value": "8507"},
    {"label": "Rare-earth metals (2805)", "value": "2805"},
    {"label": "Bird's eggs (0407)", "value": "0407"}
]

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

def get_trade_partners(reporter, flow, hs_code, year, api_key):
    params = {
        "reporterCode": reporter,
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
    return partner_values

def calculate_scri(imports, exports):
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

# Dash App Layout
app = Dash(__name__)
app.layout = html.Div([
    html.H1("📦 Supply Chain Resilience Explorer", style={"textAlign": "center", "color": "#003366"}),
    html.P("Explore critical goods supply chain metrics for any country and year.", style={"textAlign": "center"}),

    html.Label("🔑 Enter your API Key:"),
    dcc.Input(id='api-key-input', type='text', placeholder="Enter API Key", debounce=True, style={'width': '50%'}),
    dcc.Store(id='api-key-store'),
    html.Div(id='api-key-status', style={'marginBottom': '20px', 'color': 'green'}),

    html.Label("🌍 Select a Country:"),
    dcc.Dropdown(id='country-dropdown', options=[], value="826", clearable=False),

    html.Label("📅 Select a Year:"),
    dcc.Dropdown(id='year-dropdown', options=year_options, value=2022, clearable=False),

    dcc.Loading(
        id="loading-vulnerability",
        type="circle",
        children=[
            html.Div(id='top-vulnerable-output', style={"marginTop": "20px", "marginBottom": "20px"}),
            dcc.Graph(id='scri-bar-chart')
        ]
    ),

    html.Label("🛠️ Select a Commodity (HS Code):"),
    dcc.Dropdown(id='commodity-dropdown', options=commodity_options, value="8541", clearable=False),

    dcc.Loading(
        id="loading-commodity-analysis",
        type="dot",
        children=[
            html.Div(id='metrics-output', style={"marginTop": "20px", "marginBottom": "20px"}),
            dcc.Graph(id='imports-pie-chart')
        ]
    )
])

# Store API Key
@app.callback(
    [Output('api-key-store', 'data'),
     Output('api-key-status', 'children'),
     Output('country-dropdown', 'options')],
    Input('api-key-input', 'value')
)
def update_api_key_store(api_key_input):
    if api_key_input:
        countries = fetch_countries(api_key_input)
        return api_key_input, "✅ API key stored successfully.", countries
    return no_update, "", []

# Callback for Top 3 Vulnerable Goods and Bar Chart
@app.callback(
    [Output('top-vulnerable-output', 'children'),
     Output('scri-bar-chart', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('api-key-store', 'data')]
)
def get_top_vulnerable_goods(country_code, year, api_key):
    results = []
    for item in commodity_options:
        hs_code = item['value']
        label = item['label']
        imports = get_trade_partners(country_code, "M", hs_code, year, api_key)
        exports = get_trade_partners(country_code, "X", hs_code, year, api_key)
        if imports:
            scri = calculate_scri(imports, exports)
            results.append((label, scri['SCRI']))

    if not results:
        return html.Div("No data available to calculate vulnerabilities."), {}

    top3 = sorted(results, key=lambda x: x[1], reverse=True)[:3]
    bar_fig = go.Figure(go.Bar(
        x=[x[1] for x in results],
        y=[x[0] for x in results],
        orientation='h',
        marker=dict(color='firebrick')
    ))
    bar_fig.update_layout(
        title="SCRI Scores for All Critical Goods",
        xaxis_title="SCRI Score",
        yaxis_title="Commodity",
        template="plotly_white",
        height=400
    )

    return html.Div([
        html.H3("🔺 Top 3 Vulnerable Critical Goods (by SCRI)"),
        html.Ul([html.Li(f"{label}: SCRI = {scri:.4f}") for label, scri in top3])
    ]), bar_fig

# Callback for Individual Commodity Analysis with Policy Block
@app.callback(
    [Output('metrics-output', 'children'),
     Output('imports-pie-chart', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('commodity-dropdown', 'value'),
     Input('api-key-store', 'data')]
)
def update_country_analysis(country_code, year, hs_code, api_key):
    import_data = get_trade_partners(country_code, "M", hs_code, year, api_key)
    export_data = get_trade_partners(country_code, "X", hs_code, year, api_key)

    if not import_data:
        return [html.Div("No import data available for this selection."), {}]

    scri_result = calculate_scri(import_data, export_data)
    metrics_text = [
        html.H4("📊 Supply Chain Risk Metrics"),
        html.Div(f"Herfindahl-Hirschman Index (HHI): {scri_result['HHI']}"),
        html.Div(f"Supplier Diversity Score: {scri_result['Diversity Score']}"),
        html.Div(f"Import Dependency Index (IDI): {scri_result['IDI']}"),
        html.Div(f"Composite SCRI: {scri_result['SCRI']}", style={"fontWeight": "bold"}),
        html.Div(f"Total Imports (USD): {scri_result['Total Imports']:,}"),
        html.Div(f"Total Exports (USD): {scri_result['Total Exports']:,}")
    ]

    scri_score = scri_result['SCRI']
    if scri_score > 0.5:
        recommendation = html.Div([
            html.H5("⚠️ Policy Recommendation: High Supply Chain Vulnerability"),
            html.P("The SCRI score indicates a high risk. The country is heavily dependent on a few suppliers and lacks diversification."),
            html.Ul([
                html.Li("🔄 Diversify import partners by exploring new exporters of this commodity."),
                html.Li("🏭 Invest in domestic production capacity where feasible."),
                html.Li("📉 Reduce import dependency by seeking regional trade agreements or alternatives."),
                html.Li("📦 Build inventory buffers to handle disruptions.")
            ])
        ], style={
            "backgroundColor": "#f8d7da",
            "border": "1px solid #f5c6cb",
            "padding": "15px",
            "borderRadius": "6px",
            "color": "#721c24",
            "marginTop": "20px"
        })

    elif scri_score > 0.2:
        recommendation = html.Div([
            html.H5("🟡 Policy Recommendation: Medium Supply Chain Risk"),
            html.P("The SCRI score suggests moderate risk. There is room for improvement in supplier diversity or dependency."),
            html.Ul([
                html.Li("🌍 Explore and engage with new international suppliers."),
                html.Li("📈 Monitor geopolitical and economic trends in current supplier countries."),
                html.Li("📊 Encourage redundancy by balancing supplier concentration."),
                html.Li("🤝 Consider bilateral trade discussions with emerging exporters.")
            ])
        ], style={
            "backgroundColor": "#fff3cd",
            "border": "1px solid #ffeeba",
            "padding": "15px",
            "borderRadius": "6px",
            "color": "#856404",
            "marginTop": "20px"
        })

    else:
        recommendation = html.Div([
            html.H5("✅ Policy Recommendation: Resilient Supply Chain"),
            html.P("The SCRI score indicates low risk. The supply chain appears stable and well-diversified."),
            html.Ul([
                html.Li("🧭 Continue monitoring supplier performance and global risks."),
                html.Li("📌 Maintain current diversification strategies."),
                html.Li("🛡️ Invest in long-term contracts with reliable partners.")
            ])
        ], style={
            "backgroundColor": "#d4edda",
            "border": "1px solid #c3e6cb",
            "padding": "15px",
            "borderRadius": "6px",
            "color": "#155724",
            "marginTop": "20px"
        })

    metrics_text.append(recommendation)

    df_imports = pd.DataFrame(import_data.items(), columns=["partner", "value"])
    df_imports = df_imports.sort_values(by="value", ascending=False)
    if len(df_imports) > 5:
        top5 = df_imports.iloc[:5]
        other = pd.DataFrame({"partner": ["Other"], "value": [df_imports.iloc[5:]["value"].sum()]})
        df_imports = pd.concat([top5, other], ignore_index=True)

    fig = px.pie(df_imports, values='value', names='partner',
                 title=f"Import Sources for HS {hs_code} ({year})", hole=0.4)
    fig.update_layout(
        legend_title_text='Partner Country',
        height=500,
        margin=dict(t=40, b=20, l=40, r=40),
        showlegend=True,
        legend=dict(orientation="v", x=1.05, y=1)
    )

    return metrics_text, fig

# 🚀 Run App
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8055)


# In[ ]:




