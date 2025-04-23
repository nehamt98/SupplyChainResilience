#!/usr/bin/env python
# coding: utf-8
# Supply Chain Resilience Explorer Dashboard

# Required Libraries
import pandas as pd
from dash import Dash, dcc, html, Input, Output, no_update, exceptions
import plotly.express as px
import plotly.graph_objects as go
from utils.main_utils import fetch_countries, fetch_commodities, get_trade_partners, calculate_scri

# Year dropdown options
year_options = [{"label": str(y), "value": y} for y in range(2010, 2024)]

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
    dcc.Dropdown(id='country-dropdown', options=fetch_countries(), value="", clearable=False),

    html.Label("📅 Select a Year:"),
    dcc.Dropdown(id='year-dropdown', options=year_options, value=2022, clearable=False),

    html.Label("🛠️ Select a Commodity:"),
    dcc.Dropdown(id='commodity-dropdown', options=fetch_commodities(), value="", clearable=False),

    dcc.Loading(
        id="loading-commodity-analysis",
        type="dot",
        children=[
            html.Div(id='metrics-output', style={"marginTop": "20px", "marginBottom": "20px"}),
            dcc.Graph(id='imports-pie-chart')
        ]
    ),
    html.Label("📦 Select Critical Commodities to Compare:"),
    dcc.Dropdown(
        id='multi-commodity-select',
        options=fetch_commodities(),
        multi=True,
        placeholder="Select 1 or more commodities",
        style={'marginBottom': '20px'}
    ),

    dcc.Loading(
        id="loading-multi-scri",
        type="circle",
        children=[
            html.Div(id='multi-commodity-output'),
            dcc.Graph(id='multi-scri-bar-chart')
        ]
    ),
])

# Callback when API key is updated
@app.callback(
    [Output('api-key-store', 'data'),
     Output('api-key-status', 'children')],
    Input('api-key-input', 'value')
)
def update_api_key_store(api_key_input):
    if api_key_input:
        # countries = fetch_countries(api_key_input)
        return api_key_input, "✅ API key stored successfully."
    return no_update, ""

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
    if not country_code or not hs_code or not api_key:
        raise exceptions.PreventUpdate
    
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

# Callback for update in multi-commodity selection
@app.callback(
    [Output('multi-commodity-output', 'children'),
     Output('multi-scri-bar-chart', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('multi-commodity-select', 'value'),
     Input('api-key-store', 'data')]
)
def analyze_selected_commodities(country_code, year, hs_codes, api_key):
    if not hs_codes or hs_codes == [] or not country_code or api_key is None:
        raise exceptions.PreventUpdate

    results = []
    for hs_code in hs_codes:
        imports = get_trade_partners(country_code, "M", hs_code, year, api_key)
        exports = get_trade_partners(country_code, "X", hs_code, year, api_key)
        if imports:
            scri = calculate_scri(imports, exports)
            full_label = next((c['label'] for c in fetch_commodities() if c['value'] == hs_code), f"HS {hs_code}")
            short_label = (full_label[:50] + "...") if len(full_label) > 50 else full_label
            results.append({"short_label": short_label, "full_label": full_label, "scri": scri['SCRI']})

    if not results:
        return html.Div("No SCRI data available for selected commodities."), go.Figure()

    bar_fig = go.Figure(go.Bar(
        x=[item["scri"] for item in results],
        y=[item["short_label"] for item in results],
        orientation='h',
        marker=dict(color='darkcyan'),
        hovertext=[item["full_label"] for item in results],
        hoverinfo="text+x"
    ))
    bar_fig.update_layout(
        title="SCRI Scores for Selected Commodities",
        xaxis_title="SCRI Score",
        yaxis_title="Commodity",
        template="plotly_white",
        height=400
    )

    return html.Div([
        html.H4("🔍 SCRI Scores for Selected Commodities"),
        html.Ul([html.Li(f"{item['full_label']}: SCRI = {item['scri']:.4f}") for item in results])
    ]), bar_fig

# Run App
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8055)
