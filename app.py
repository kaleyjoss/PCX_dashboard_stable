import dash
from dash import Dash, dcc, html, callback, Input, Output, dash_table
from flask import send_from_directory
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
import json
from datetime import datetime as dt
from dash import page_container
import os
app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], use_pages=True,  pages_folder="pages")

server = app.server   # get the Flask server inside Dash

# folder where your reports live
REPORTS_DIR = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/fmriprep_reports')
project = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/behavioral')
tracker_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


def extract_survey_date(filename):
    datestr = filename.split('_')[-1].split('.')[0]
    try:
        date_obj = dt.strptime(datestr, '%b %d, %Y')
        if date_obj is not None and isinstance(date_obj, dt):
            return date_obj
    except Exception as e:
        logging.debug(f"no datetime in {filename}: {e}")
    
    return None
    
def get_most_recent_survey(directory, recoded=False):
    # Allowed Excel extensions
    extensions = (".csv", ".xls", ".xlsx")
    filenames = [f for f in os.listdir(directory) if f.endswith(extensions)]
    if recoded==True:
        filenames = [f for f in filenames if 'recoded' in f]
    else:
        filenames = [f for f in filenames if not 'recoded' in f]
    
    # List Excel files with their sizes
    dates = []
    for filename in filenames:

        survey_date = extract_survey_date(filename)
        if survey_date is not None:
            dates.append({'filename': filename, 'date': survey_date})
            logging.debug(f'filename={filename} -> date={extract_survey_date(filename)}')

    if len(dates) > 0:
        dates.sort(key=lambda file: file['date'], reverse=True)
        logging.debug(dates)
        return os.path.join(directory, dates[0]['filename'])
    
    return None


survey_names = ['clinical_administered_data','clinical_self_report_data',
                     'mri_self_report_data','supplemental_self_report_data']

surveys={}
recoded_surveys={}
for root, dirs, files in os.walk(project):
    for survey in survey_names: 
        if survey in dirs: 
            surveys[survey] = []
            survey_dir = os.path.join(root, survey)
            try:
                filepath = get_most_recent_survey(survey_dir)
                filepath_recoded = get_most_recent_survey(survey_dir, recoded=True)
            except Exception as e:
                logging.error(f'For survey_dir {survey_dir}, {e}')
            if filepath is not None:
                logging.debug(f'most recent survey for {survey}: {os.path.basename(filepath)}')
                surveys[survey] = pd.read_csv(filepath)
                recoded_surveys[survey]=pd.read_csv(filepath_recoded)

first_df = surveys['clinical_administered_data']
subject_ids = first_df['SUBJECT_ID'].unique()



# Flask route to serve files from REPORTS_DIR
@server.route("/reports/<path:filename>")
def serve_report(filename):
    full_path = os.path.join(REPORTS_DIR, filename)
    print(f"full_path {full_path}")
    directory, filename = os.path.split(full_path)
    print(f"Serving report from {directory} {filename}")
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
        dcc.Dropdown(subject_ids, id='subject-picker',clearable=False, value='qualr200'),
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
    dcc.Store(id='subject-id'),
    html.Div([
        page_container  # ← REQUIRED to show the current page content here
    ], style={"padding": "2rem", 'margin': '0 auto', 'max-width': '1200px'}),
])


@callback(
    Output(component_id='subject-id', component_property='data'),
    Input(component_id='subject-picker', component_property='value')
)
def update_subject(subject):
    return subject


    
if __name__ == "__main__":
    app.run(debug=True, port=8090)

