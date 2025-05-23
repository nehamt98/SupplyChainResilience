#!/usr/bin/env python
# coding: utf-8
# Supply Chain Resilience Explorer Dashboard

# Required Libraries
import pandas as pd
from dash import Dash, dcc, html, Input, Output, no_update, exceptions
import plotly.express as px
import plotly.graph_objects as go
from utils.main_utils import fetch_countries, fetch_commodities, calculate_scri, get_top_exporters, get_trade_info

# Year dropdown options
year_options = [{"label": str(y), "value": y} for y in range(2023, 2010, -1)]

# Sector options
# Add your sector here
sector_options = [
            {"label": "Semiconductors", "value": "semiconductors"},
            {"label": "Public Health", "value": "public_health"},
            {"label": "Energy", "value": "energy"},
        ]

# Dash App Layout
app = Dash(__name__, external_stylesheets=[
    "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"
])
app.layout = html.Div([
    # Header
    html.Header([
        html.H1("📦 Supply Chain Resilience Explorer", style={"textAlign": "center", "fontWeight": "bold", "fontSize": "30px"}),
        html.P("Explore critical goods supply chain metrics for any country and year.",
               style={"textAlign": "center", "fontSize": "14px", "color": "gray"})
    ], style={"marginBottom": "30px"}),

    # Top Controls Grid
    html.Div([
        html.Div([
            html.Label("🔑 API Key", style={"fontWeight": "600", "marginRight": "10px"}),
            dcc.Input(
                id='api-key-input',
                type='text',
                placeholder="Enter API Key",
                debounce=True,
                className='border rounded p-2',
                style={"width": "300px"}
            )
        ], style={"display": "flex", "alignItems": "center"}),  # align label and input inline

        dcc.Store(id='api-key-store'),
        html.Div(id='api-key-status', style={'marginTop': '5px', 'color': 'green'})
    ], className="mb-8"),

    html.Div([
        html.Div([
            html.Label("🌍 Country", style={"fontWeight": "600"}),
            dcc.Dropdown(id='country-dropdown', options=fetch_countries(), value="", clearable=False,
                         className='select', style={'width': '100%'})
        ]),
        html.Div([
            html.Label("📅 Year", style={"fontWeight": "600"}),
            dcc.Dropdown(id='year-dropdown', options=year_options, clearable=False,
                         className='select', style={'width': '100%'})
        ]),
         html.Div([
            html.Label("🌐 Sector", style={"fontWeight": "600"}),
            dcc.Dropdown(id='sector-dropdown', options=sector_options, clearable=False,
                         className='select', style={'width': '100%'})
        ])
    ], className="grid grid-cols-1 md:grid-cols-3 gap-3"),

    html.Div([
        html.Label("📦 Commodity", style={"fontWeight": "600", "marginBottom": "8px"}),
        dcc.Dropdown(id='commodity-dropdown', clearable=False,
                        className='select', style={'width': '100%'})
    ], style={"marginBottom": "30px"}),


    # Risk Metrics and Summary
    dcc.Loading(
        id="loading-commodity-analysis",
        type="dot",
        children=html.Div([
            # Metric cards inside loading
            html.Div(
                id="summary-metric-cards",
                className="grid grid-cols-1 md:grid-cols-4 gap-4",
                style={"marginBottom": "20px"}
            ),
            html.Div([
                # Left: Metrics Panel
                html.Div(
                    id='metrics-output',
                    children=[
                        html.Div(
                            "📊 Supply Chain Risk Metrics will appear here after selection.",
                            style={
                                "display": "flex",
                                "justifyContent": "center",
                                "alignItems": "center",
                                "height": "100%",
                                "width": "100%",
                                "color": "gray",
                                "fontStyle": "italic",
                                "textAlign": "center"
                            }
                        )
                    ],
                    className="bg-white shadow rounded-xl p-4",
                    style={
                        "minHeight": "320px",
                        "display": "flex",
                        "flexBasis": "25%",
                        "flexGrow": "1",
                        "width": "100%"
                    }
                ),

                # Middle: Pie Chart Panel
                html.Div(
                    dcc.Graph(
                        id='imports-pie-chart',
                        style={"height": "280px", "width": "100%"}
                    ),
                    className="bg-white shadow rounded-xl p-4",
                    style={
                        "minHeight": "320px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "flexBasis": "35%",
                        "flexGrow": "1",
                        "minWidth": 0
                    }
                ),

                # Right: Policy Panel
                html.Div(
                    id='policy-panel',
                    children=[
                        html.Div(
                            "⚠️ Policy Recommendations will appear here after selection.",
                            style={
                                "display": "flex",
                                "justifyContent": "center",
                                "alignItems": "center",
                                "height": "100%",
                                "width": "100%",
                                "color": "gray",
                                "fontStyle": "italic",
                                "textAlign": "center"
                            }
                        )
                    ],
                    className="bg-white shadow rounded-xl p-4",
                    style={
                        "minHeight": "320px",
                        "display": "flex",
                        "flexBasis": "40%",
                        "flexGrow": "1",
                        "minWidth": 0
                    }
                )
            
            ],
            className="flex flex-col md:flex-row gap-4 w-full",
            style={"marginBottom": "30px"})
        ]),
    ),

    # Comparison Section
    html.Div([
        html.Label("📊 Compare Commodities", style={"fontWeight": "600", "marginBottom": "8px"}),
        dcc.Dropdown(
            id='multi-commodity-select',
            multi=True,
            placeholder="Select 1 or more commodities",
            className='select',
            style={'width': '100%'}
        ),
        dcc.Loading(
            id="loading-multi-scri",
            type="circle",
            children=[
                html.Div(id='multi-commodity-output', style={"marginBottom": "20px"}),
                dcc.Graph(id='multi-scri-bar-chart', style={"height": "250px"})
            ]
        )
    ], className="bg-white shadow p-4 rounded-xl", style={"marginBottom": "30px", "minHeight": "600px"}),
], className="p-4 space-y-6")

# Callback when API key is updated
@app.callback(
    [Output('api-key-store', 'data'),
     Output('api-key-status', 'children')],
    Input('api-key-input', 'value')
)
def update_api_key_store(api_key_input):
    if api_key_input:
        return api_key_input, "✅ API key stored successfully."
    return no_update, ""

# Callback when sector is updated
@app.callback(
    [Output('commodity-dropdown', 'options'),
     Output('multi-commodity-select', 'options')],
     Input('sector-dropdown', 'value')
)
def update_commodity_dropdown(selected_sector):
    if not selected_sector:
        raise exceptions.PreventUpdate
    # Update the commodities dropdown
    options = fetch_commodities(selected_sector)
    return options, options if options else None

# Callback for Individual Commodity Analysis
@app.callback(
    [Output('summary-metric-cards', 'children'),
     Output('metrics-output', 'children'),
     Output('imports-pie-chart', 'figure'),
     Output('policy-panel', 'children')],
    [Input('country-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('commodity-dropdown', 'value'),
     Input('api-key-store', 'data')]
)
def update_country_analysis(country_code, year, hs_code, api_key):
    if not country_code or not hs_code or not api_key:
        raise exceptions.PreventUpdate
    
    # Get import and export data to calculate scores
    import_data, export_data, export_count = get_trade_info(country_code, hs_code, year, api_key)

    # Populate when data is missing
    if not import_data:
        return (
            html.Div(
                "⚠️ No import data available for this selection.",
                style={"textAlign": "center", "color": "gray", "paddingTop": "20px"}
            ),
            go.Figure(), 
            html.Div(
                "⚠️ No policy recommendations available due to missing data.",
                style={"textAlign": "center", "color": "gray", "paddingTop": "20px"}
            )
        )

    # Calculate the scores
    scri_result = calculate_scri(import_data, export_data, export_count)

    # Populate the score cards
    metric_cards = [
        html.Div([
            html.Div([
                html.Div("Herfindahl–Hirschman Index (HHI)", className="text-sm font-semibold text-gray-700"),
                html.Div(f"{scri_result['HHI']:.4f}", className="text-2xl font-bold mt-1"),
                html.Div("Indicates how concentrated imports are among supplier countries.", className="text-sm mt-2 text-gray-600"),
            ]),
            html.Div("The higher the score, the greater the risk", className="text-xs text-gray-500 mt-4")
        ], className="border rounded-lg p-4 shadow bg-white flex flex-col justify-between"),

        html.Div([
            html.Div([
                html.Div("Supplier Diversity Score", className="text-sm font-semibold text-gray-700"),
                html.Div(f"{scri_result['Diversity Score']:.4f}", className="text-2xl font-bold mt-1"),
                html.Div("Measures how diversified a country’s supplier base is compared to global availability.", className="text-sm mt-2 text-gray-600"),
            ]),
            html.Div("The lower the score, the greater the risk", className="text-xs text-gray-500 mt-4")
        ], className="border rounded-lg p-4 shadow bg-white flex flex-col justify-between"),

        html.Div([
            html.Div([
                html.Div("Import Dependency Index (IDI)", className="text-sm font-semibold text-gray-700"),
                html.Div(f"{scri_result['IDI']:.4f}", className="text-2xl font-bold mt-1"),
                html.Div("Shows how much a country relies on imports for this product.", className="text-sm mt-2 text-gray-600"),
            ]),
            html.Div("The higher the score, the greater the risk", className="text-xs text-gray-500 mt-4")
        ], className="border rounded-lg p-4 shadow bg-white flex flex-col justify-between"),

        html.Div([
            html.Div([
                html.Div("Composite SCRI", className="text-sm font-semibold text-gray-700"),
                html.Div(f"{scri_result['SCRI']:.4f}", className="text-3xl font-extrabold mt-1 text-gray-900"),
                html.Div("Aggregated risk score from HHI, Diversity, and IDI.", className="text-sm mt-2 text-gray-600"),
            ]),
            html.Div("The higher the score, the greater the risk", className="text-xs text-gray-500 mt-4")
        ], className="bg-blue-50 border border-blue-200 rounded-lg p-4 shadow flex flex-col justify-between")
    ]

    # Populate left panel - Bar chart for Imports vs Exports
    import_value = scri_result["Total Imports"]
    export_value = scri_result["Total Exports"]

    import_export_fig = go.Figure(
        data=[
            go.Bar(name="Imports", x=["Trade Value"], y=[import_value], marker_color="teal", text=[f"${import_value:,.0f}"]),
            go.Bar(name="Exports", x=["Trade Value"], y=[export_value], marker_color="orange", text=[f"${export_value:,.0f}"])
        ]
    )
    import_export_fig.update_layout(
        barmode="group",
        title=f"Total Import vs Export",
        yaxis_title="Value (USD)",
        xaxis_title=None,
        template="plotly_white",
        height=280,
        margin=dict(t=40, b=40, l=40, r=10),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.2)
    )

    # Optional banner if exports > imports
    banner = None
    if export_value > import_value:
        banner = html.Div("🚨 This country is a net exporter of this good.",
                        className="text-red-600 text-sm font-semibold mb-2 text-center")

    # Final component: banner + chart
    metrics_text = html.Div(
        children=[
            html.Div(
                banner if banner else "",
                style={
                    "height": "24px", 
                    "textAlign": "center"
                }
            ),
            dcc.Graph(
                figure=import_export_fig,
                style={"flexGrow": "1", "width": "100%"}
            )
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "alignItems": "stretch",
            "height": "100%",
            "width": "100%"
        }
    ) 

    # Populate pie chart
    df_imports = pd.DataFrame(import_data.items(), columns=["partner", "value"])
    df_imports = df_imports.sort_values(by="value", ascending=False)
    if len(df_imports) > 5:
        top5 = df_imports.iloc[:5]
        other = pd.DataFrame({"partner": ["Other"], "value": [df_imports.iloc[5:]["value"].sum()]})
        df_imports = pd.concat([top5, other], ignore_index=True)

    fig = px.pie(df_imports, values='value', names='partner',
                 title=f"Import Sources for HS {hs_code} ({year})", hole=0.4)
    total = df_imports['value'].sum()
    fig.update_traces(
        texttemplate=[
            f'{p:.1f}%' if p >= 4 else ''
            for p in 100 * df_imports['value'] / total
        ]
    )

    fig.update_layout(
        title={
            'text': f"Import Sources for HS {hs_code} ({year})",
            'x': 0.5,
            'xanchor': 'center',
            'font': {"size": 16}
        },
        height=280,
        margin=dict(t=30, b=20, l=10, r=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1,
            y=0.5,
            xanchor="left",
            valign="middle"
        )
    )

    # Populate right panel
    scri_score = scri_result['SCRI']
    if scri_score > 0.65:
        recommendation_children = [
            html.H4("⚠️ Policy Recommendation: High Supply Chain Vulnerability", style={"fontWeight": "600"}),
            html.P("The SCRI indicates a high risk. The country is heavily dependent on a few suppliers and lacks diversification."),
            html.Ul([
                html.Li("🔄 Diversify import partners by exploring new exporters of this commodity."),
                html.Li("🏭 Invest in domestic production capacity where feasible."),
                html.Li("📉 Reduce import dependency by seeking regional trade agreements or alternatives."),
                html.Li("📦 Build inventory buffers to handle disruptions.")
            ], className="list-disc ml-5 mt-2 space-y-1 text-sm")
        ]
        panel_style = {
            "backgroundColor": "#f8d7da",  # light red
            "border": "1px solid #f5c6cb",
            "color": "#721c24",
            "width": "100%"
        }
        # Get top_exporters
        top_exporters = get_top_exporters(country_code, hs_code, year, import_data, api_key)
        exporter_suggestions = html.Ul([
            html.Li(f"{export_details[1]}: ${export_details[0]:,.0f}")
            for _, export_details in top_exporters.items()
        ], className="list-disc ml-5 text-sm mt-2 space-y-1") if top_exporters else None
        
        if exporter_suggestions:
            recommendation_children += [
                html.H4("🌍 Suggested New Trade Partners (Top Exporters)", style={"fontWeight": "600", "marginTop": "20px"}),
                html.P("Consider exploring imports from these top global exporters of this good:"),
                exporter_suggestions
            ]

    elif scri_score > 0.35:
        recommendation_children = [
            html.H4("🟡 Policy Recommendation: Medium Supply Chain Risk", style={"fontWeight": "600"}),
            html.P("The SCRI suggests moderate risk. There is room for improvement in supplier diversity or dependency."),
            html.Ul([
                html.Li("🌍 Explore and engage with new international suppliers."),
                html.Li("📈 Monitor geopolitical and economic trends in current supplier countries."),
                html.Li("📊 Encourage redundancy by balancing supplier concentration."),
                html.Li("🤝 Consider bilateral trade discussions with emerging exporters.")
            ], className="list-disc ml-5 mt-2 space-y-1 text-sm")
        ]
        panel_style = {
                "backgroundColor": "#fff3cd",  # light yellow
                "border": "1px solid #ffeeba",
                "color": "#856404",
                "width": "100%"
            }
        
        # Get top_exporters
        top_exporters = get_top_exporters(country_code, hs_code, year, import_data, api_key)
        exporter_suggestions = html.Ul([
            html.Li(f"{export_details[1]}: ${export_details[0]:,.0f}")
            for _, export_details in top_exporters.items()
        ], className="list-disc ml-5 text-sm mt-2 space-y-1") if top_exporters else None

        if exporter_suggestions:
            recommendation_children += [
                html.H4("🌍 Suggested New Trade Partners (Top Exporters)", style={"fontWeight": "600", "marginTop": "20px"}),
                html.P("Consider exploring imports from these top global exporters of this good:"),
                exporter_suggestions
            ]

    else:
        recommendation_children = [
            html.H5("✅ Policy Recommendation: Resilient Supply Chain", style={"fontWeight": "600"}),
            html.P("The SCRI indicates low risk. The supply chain appears stable and well-diversified."),
            html.Ul([
                html.Li("🧭 Continue monitoring supplier performance and global risks."),
                html.Li("📌 Maintain current diversification strategies."),
                html.Li("🛡️ Invest in long-term contracts with reliable partners.")
            ], className="list-disc ml-5 mt-2 space-y-1 text-sm")
        ]
        panel_style = {
            "backgroundColor": "#d4edda",  # light green
            "border": "1px solid #c3e6cb",
            "color": "#155724",
            "width": "100%"
        }

    # Final recommendation component
    policy_panel = html.Div(
        recommendation_children,
        className="rounded-xl p-4 w-full",
        style=panel_style
    )

    return metric_cards, metrics_text, fig, policy_panel

# Callback for update in multi-commodity selection
@app.callback(
    [Output('multi-commodity-output', 'children'),
     Output('multi-scri-bar-chart', 'figure')],
    [Input('country-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('multi-commodity-select', 'value'),
     Input('api-key-store', 'data'),
     Input('sector-dropdown', 'value')]
)
def analyze_selected_commodities(country_code, year, hs_codes, api_key, sector):
    if not hs_codes or hs_codes == [] or not country_code or api_key is None:
        # show placeholder text and an empty figure when nothing is selected
        placeholder = html.Div(
            "🔍 Select 1 or more commodities above to see their SCRIs",
            style={"textAlign": "center", "color": "gray", "marginTop": "20px"}
        )
        empty_fig = go.Figure()
        return placeholder, empty_fig

    # Get import and export data for each commodity
    results = []
    for hs_code in hs_codes:
        imports, exports, export_count = get_trade_info(country_code, hs_code, year, api_key)

        if imports:
            scri = calculate_scri(imports, exports, export_count)
            full_label = next((c['label'] for c in fetch_commodities(sector) if c['value'] == hs_code), f"HS {hs_code}")
            short_label = (full_label[:50] + "...") if len(full_label) > 50 else full_label
            results.append({"short_label": short_label, "full_label": full_label, "scri": scri['SCRI']})

    if not results:
        return html.Div(
            "No SCRI data available for selected commodities.",
            style={"textAlign": "center", "color": "gray", "marginTop": "10px"}
        ), go.Figure()

    # Bar chart
    bar_fig = go.Figure(go.Bar(
        x=[item["scri"] for item in results],
        y=[item["short_label"] for item in results],
        orientation='h',
        marker=dict(color='darkcyan'),
        hovertext=[item["full_label"] for item in results],
        hoverinfo="text+x",
        text=[f"{item['scri']:.2f}" for item in results],   
        textposition='auto'
    ))
    bar_fig.update_layout(
        xaxis_title="SCRI",
        yaxis_title="Commodity",
        template="plotly_white",
        height=400,
        margin=dict(t=40, l=60, r=20, b=40)
    )

    return html.Div(children=[
            html.H4("🔍 SCRIs for Selected Commodities", style={
                "fontWeight": "600",
                "fontSize": "18px",
                "marginTop": "20px"
            })
        ]), bar_fig

# Run App
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8055)
