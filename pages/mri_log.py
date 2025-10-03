import os
import sys
import re
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import pickle
import os
import sys
import inspect

# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
from scripts.paths import get_path, tracker_df, rmr_df, subs_df, pcx_dir, mri_dir, data_dir
import scripts.sub_id as sub_id
from scripts.surveys import subject_ids, surveys, recoded_surveys, subsurvey_key
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])


# Register page into dash app as pagename
dash.register_page(__name__, path="/mri_log", title='MRI Report', name='MRI Report')


subjects = os.listdir(mri_dir)

# App layout
layout = html.Div([
    html.H1('Data by Subject', style={'margin':20}),
    html.Iframe(
        id='report_location', style={"width": "100%", "height": "800px"}
    )


])

# Add controls to build the interaction
@callback(
    Output(component_id='report_location', component_property='src'),
    Input(component_id='subject-id', component_property='data'),
)

def cb(subject_id):
    if subject_id is None:
        return None
    pcrid = subject_id.replace('qualr', 'sub-PCR').replace('qualm', 'sub-PCM')
    """Callback to update the filepath based on the selected id"""
    return f"/reports/{pcrid}.html/index.html"

