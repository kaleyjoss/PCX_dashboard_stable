import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
from flask import send_from_directory
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
from dash import page_container
import os
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], use_pages=True,  pages_folder="pages")

server = app.server   # get the Flask server inside Dash

# folder where your reports live
REPORTS_DIR = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/fmriprep_reports')

# Flask route to serve files from REPORTS_DIR
@server.route("/reports/<path:filename>")
def serve_report(filename):
    full_path = os.path.join(REPORTS_DIR, filename)
    directory, filename = os.path.split(full_path)
    return send_from_directory(directory, filename)


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Sidebar with navigation
sidebar = html.Div(
    [
        html.H2("PCX Study", className="display-4"),
        html.Hr(),
        html.P("Interactive dashboard for the PCX study.", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Passive Data", href="/passive_data", active="exact"),
                dbc.NavLink("Survey Data", href="/survey_data", active="exact"),
                dbc.NavLink("MRI Logs", href="/mri_log", active="exact"),

            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

app.layout = html.Div([
    sidebar,
    html.Div([
        page_container  # ← REQUIRED to show the current page content here
    ], style={"padding": "2rem", 'margin': '0 auto', 'max-width': '1200px'}),
])


    
if __name__ == "__main__":
    app.run(debug=True, port=8090)

