import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime

# 1. Database Connection
engine = create_engine('postgresql://admin:fraud_detection@localhost:5432/fraud_detection')

app = dash.Dash(__name__)

# 2. Premium Forensic Layout
app.layout = html.Div(style={
    'backgroundColor': '#000000', 'color': '#FFFFFF',
    'fontFamily': 'monospace', 'padding': '20px', 'height': '100vh', 'overflow': 'hidden'
}, children=[

    # --- HEADER ---
    html.Div([
        html.Div([
            html.H1("NEURAL_WATCH // FORENSIC_LAB",
                    style={'color': '#00FF9C', 'fontSize': '18px', 'margin': '0', 'letterSpacing': '3px'}),
            html.P("MODE: BIO-METRIC_USER_SCAN // LOCATION: CHENNAI_NODE", style={'color': '#444', 'fontSize': '10px'})
        ], style={'flex': '1'}),
        html.Div(id='live-clock', style={'color': '#00FF9C', 'fontSize': '14px', 'marginTop': '5px'})
    ], style={'display': 'flex', 'borderBottom': '1px solid #111', 'paddingBottom': '10px', 'marginBottom': '20px'}),

    # --- TOP CONTROL BAR ---
    html.Div([
        html.Div([
            html.Label("CITY_FILTER", style={'fontSize': '10px', 'color': '#888', 'letterSpacing': '1px'}),
            dcc.Dropdown(
                id='city-dropdown',
                options=[{'label': i, 'value': i} for i in
                         ['Chennai', 'Mumbai', 'Bangalore', 'Delhi', 'Hyderabad', 'Kochi']],
                placeholder="ALL_NODES",
                style={'backgroundColor': '#000', 'color': '#000'}
            ),
        ], style={'width': '250px'}),
        html.Div([
            html.P("TOTAL_VALUE_SCAN", style={'fontSize': '10px', 'color': '#888', 'margin': '0'}),
            html.H3(id='live-volume', style={'color': '#FFF', 'margin': '0', 'fontWeight': '300'})
        ], style={'marginLeft': '50px'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),

    # --- MAIN GRID ---
    html.Div(style={'display': 'flex', 'gap': '20px', 'height': '70vh'}, children=[

        # LEFT: User ID Treemap
        html.Div(style={'flex': '1', 'border': '1px solid #111', 'backgroundColor': '#050505'}, children=[
            html.P("USER_ID_DENSITY_MAP", style={'padding': '10px', 'fontSize': '10px', 'color': '#444'}),
            dcc.Graph(id='user-treemap', config={'displayModeBar': False}, style={'height': '90%'})
        ]),

        # CENTER: Main Stream (The interactive part)
        html.Div(style={'flex': '2', 'border': '1px solid #111', 'backgroundColor': '#050505', 'position': 'relative'},
                 children=[
                     html.P("VECTOR_STREAM (SELECT NODE TO INSPECT)",
                            style={'padding': '10px', 'fontSize': '10px', 'color': '#00FF9C'}),
                     dcc.Graph(id='main-stream', config={'displayModeBar': False}, style={'height': '90%'})
                 ]),

        # RIGHT: Inspector Panel
        html.Div(style={'flex': '1', 'border': '1px solid #111', 'backgroundColor': '#050505', 'display': 'flex',
                        'flexDirection': 'column'}, children=[
            html.P("TRANSACTION_INSPECTOR",
                   style={'padding': '10px', 'fontSize': '10px', 'color': '#00FF9C', 'borderBottom': '1px solid #111'}),
            html.Div(id='inspector-panel',
                     style={'padding': '20px', 'fontSize': '11px', 'lineHeight': '2', 'color': '#888'})
        ])
    ]),

    dcc.Interval(id='refresh-gate', interval=2000, n_intervals=0)
])


# 3. Combined Logic Callback
@app.callback(
    [Output('main-stream', 'figure'),
     Output('user-treemap', 'figure'),
     Output('live-volume', 'children'),
     Output('live-clock', 'children')],
    [Input('refresh-gate', 'n_intervals'),
     Input('city-dropdown', 'value')]
)
def update_dashboard(n, selected_city):
    query = "SELECT * FROM analyzed_transactions"
    if selected_city:
        query += f" WHERE city = '{selected_city}'"
    query += " ORDER BY txn_time DESC LIMIT 100"

    df = pd.read_sql(query, engine)

    if df.empty:
        return go.Figure(), go.Figure(), "₹0", "--:--:--"

    # Main Stream Graph - Using LOG SCALE for better density
    fig_stream = go.Figure()
    fig_stream.add_trace(go.Scatter(
        x=df['txn_time'],
        y=df['amount'],
        mode='markers',
        customdata=np.stack((df['user_id'], df['merchant_category'], df['is_fraud'], df['city']), axis=-1),
        marker=dict(
            size=14,
            color=df['normalized_risk'],
            colorscale='Reds',
            showscale=False,
            line=dict(width=1, color='white'),
            opacity=0.8
        )
    ))

    fig_stream.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=10, t=10, b=40),
        xaxis=dict(gridcolor='#111', zeroline=False, color='#444'),
        yaxis=dict(type='log', gridcolor='#111', zeroline=False, color='#444')
    )

    # User ID Treemap
    user_counts = df['user_id'].value_counts().reset_index()
    user_counts.columns = ['user_id', 'count']
    fig_tree = go.Figure(go.Treemap(
        labels=user_counts['user_id'],
        parents=[""] * len(user_counts),
        values=user_counts['count'],
        marker=dict(colorscale='Greens', line=dict(width=1, color='#000')),
        textinfo="label"
    ))
    fig_tree.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0))

    volume = f"₹{df['amount'].sum():,.0f}"
    clock = datetime.now().strftime("%H:%M:%S")

    return fig_stream, fig_tree, volume, clock


# 4. Inspector Callback (The Interactive Logic)
@app.callback(
    Output('inspector-panel', 'children'),
    [Input('main-stream', 'clickData')]
)
def run_inspector(clickData):
    if not clickData:
        return html.Div([
            html.P("SYSTEM_READY...", style={'color': '#00FF9C'}),
            html.P("WAITING_FOR_VECTOR_SELECTION_INPUT", style={'fontSize': '10px', 'color': '#444'})
        ])

    # Extract data from the clicked point
    data = clickData['points'][0]
    user = data['customdata'][0]
    cat = data['customdata'][1]
    is_fraud = str(data['customdata'][2]) == 'True'
    city = data['customdata'][3]
    val = data['y']

    verdict_color = "#FF004D" if is_fraud else "#00FF9C"
    verdict_text = "CRITICAL_FRAUD" if is_fraud else "VERIFIED_CLEAN"

    return html.Div([
        html.Div(style={'borderLeft': f'4px solid {verdict_color}', 'paddingLeft': '15px'}, children=[
            html.H3(f"TARGET: {user}", style={'margin': '0', 'color': '#FFF', 'fontSize': '16px'}),
            html.P(f"ORIGIN: {city}", style={'fontSize': '10px', 'margin': '5px 0', 'color': '#888'}),
            html.Hr(style={'borderColor': '#222', 'margin': '15px 0'}),
            html.P([html.Span("SEC_CATEGORY: ", style={'color': '#444'}), html.Span(cat, style={'color': '#FFF'})]),
            html.P([html.Span("TRANS_VALUE: ", style={'color': '#444'}),
                    html.Span(f"₹{val:,.2f}", style={'color': '#FFF'})]),
            html.Div(
                verdict_text,
                style={
                    'marginTop': '30px', 'padding': '8px', 'textAlign': 'center',
                    'border': f'1px solid {verdict_color}', 'color': verdict_color,
                    'fontSize': '11px', 'fontWeight': 'bold', 'letterSpacing': '3px'
                }
            )
        ])
    ])


if __name__ == '__main__':
    app.run(debug=True)
