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
import inspect

# Import custom scripts
project_dir = os.path.basename(os.getcwd())
sys.path.append(project_dir)
from scripts.update_dataframes import update_dfs
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])


# Register page into dash app as pagename
dash.register_page(__name__, path="/mri_log", title='MRI Report', name='MRI Report')

# Set PCX Project Data path
pcx_dir = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX')
mri_dir = os.path.join(pcx_dir, 'fmriprep_reports')
subjects = os.listdir(mri_dir)

# App layout
layout = html.Div([
    html.H1('Data by Subject', style={'margin':20}),
    dcc.Dropdown(id="subject_id", value='sub-PCR200', clearable=False,
        options=[{"label": f'{y.replace('.html','')}', "value": y} for y in subjects]),
    html.Iframe(
        id='report_location', style={"width": "100%", "height": "800px"}
    )


])

# Add controls to build the interaction
@callback(
    Output(component_id='report_location', component_property='src'),
    Input(component_id='subject_id', component_property='value'),
)

def cb(subject_id):
    """Callback to update the filepath based on the selected id"""
    return f"/reports/{subject_id}/index.html"

