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
dash.register_page(__name__, path="/subject")

# Set PCX Project Data path
pcx_dir = os.path.expanduser("~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2")

# Update DFs
subs_df, mindlamp_df, selected_cols, readable_cols = update_dfs(pcx_dir)
power_df = mindlamp_df[mindlamp_df['sensor']=='power']
accel_df = mindlamp_df[mindlamp_df['sensor']=='accel']
gps_df = mindlamp_df[mindlamp_df['sensor']=='gps']

# App layout
layout = html.Div([
    html.H1('Data by Subject'),
    dcc.Dropdown(id="subject_id", value='sub-PCX-PCT927', clearable=False,
        options=[{"label": f'{y}', "value": y} for y in power_df['subject_id'].unique()]),
    dcc.RadioItems(id='days', value='All days', 
        options=['All days','Weekdays','Weekends']),

    dcc.Graph(figure={}, id='phone_use-graph'),
    dcc.Graph(figure={}, id='daily_phoneuse-graph'),
    dcc.Graph(figure={}, id='activity-graph'),
    dcc.Graph(figure={}, id='gps-graph')

])

# Add controls to build the interaction
@callback(
    Output(component_id='phone_use-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = power_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Phone Activity (minutes each hour) for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

# Add controls to build the interaction
@callback(
    Output(component_id='daily_phoneuse-graph', component_property='figure'),
    Input(component_id='days', component_property='value')
)


def cb(days):
    """Callback to update the figure based on the selected id"""
    if days == 'All days':
        power_df_filtered = power_df
    elif days == 'Weekdays':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('6|7')]
    
    fig = px.line(power_df_filtered, x='day', y='daily_mins', color='subject_id', title=f'Phone Activity (minutes each hour) for each subject', 
                  height=400, width=600)
    return fig


# Add controls to build the interaction
@callback(
    Output(component_id='activity-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)

def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = accel_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Physical Activity (acceleration speed) minutes each hour for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig



@callback(
    Output(component_id='gps-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = gps_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Mobility (distance each hour) for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

"""Callback to update the figure based on the selected id"""
sub = 'sub-PCX-PCT927'
sub_df = accel_df.query("subject_id == @sub")
logging.info(sub_df.head())
