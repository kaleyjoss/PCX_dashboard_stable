import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
from dash import page_container

app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], use_pages=True,  pages_folder="pages")

# subs_df=pd.read_excel('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/Subject_tracker_PCR.xlsx', sheet_name='clean_data')
# subject_ids = subs_df['PCR ID'].unique()

# clinRatings=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')
# supp=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_SupplementalBattery/PCX_SupplementalBattery_June 18, 2025_17.12.csv')
# fmriBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_fMRIVisit_SelfReport/PCX_fMRIVisit_SelfReport_June 18, 2025_17.13.csv')
# clinBattery=pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/behavioral/PCX_ClinicalVisit_ClinicianRatings/PCX_ClinicalVisit_ClinicianRatings_June 18, 2025_17.59.csv')

# # Skip displaying some irrelevant fields if necessary, change
# heatmap_columns = subs_df.columns.to_list()
# subs_df_binary = subs_df.fillna(0)
# subs_df_filtered = subs_df_binary.loc[subs_df_binary['Clinical Interview Session Date'] != 0, :]


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
                dbc.NavLink("By Subject", href="/passive_data", active="exact"),
                dbc.NavLink("Dashboard", href="/surveys", active="exact"),
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
    ], style={"padding": "2rem"}),
])


    
if __name__ == "__main__":
    app.run(debug=True, port=8090)

