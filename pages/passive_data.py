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
import os
import sys


# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.surveys import subject_ids, surveys, recoded_surveys, subsurvey_key
from scripts.update_dataframes import update_dfs
from scripts.paths import get_path, project_dir, tracker_df, rmr_df, subs_df, pcx_dir, mri_dir, data_dir
import scripts.paths as paths

# Register page into dash app as pagename
dash.register_page(__name__, path="/passive_data", title='Passive Data', name='Passive Data')


subs_df, mindlamp_df, selected_cols, readable_cols = update_dfs(pcx_dir)
power_df = mindlamp_df[mindlamp_df['sensor']=='power']
accel_df = mindlamp_df[mindlamp_df['sensor']=='accel']
gps_df = mindlamp_df[mindlamp_df['sensor']=='gps']



# App layout
layout = html.Div([
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
    Input(component_id='subject-id', component_property='data'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    if subject_id is None:
        return None
    sub_clean = subject_id.lower().replace('_','').replace('qualr','PCX-PCR').replace('qualm','PCX-PCM')
    sub = f'sub-{sub_clean}'
    sub_df = power_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Phone Activity (minutes each hour) for {sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

# Add controls to build the interaction
@callback(
    Output(component_id='daily_phoneuse-graph', component_property='figure'),
    Input(component_id='subject-id', component_property='data'),
    Input(component_id='days', component_property='value')
)

def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    if days == 'All days':
        power_df_filtered = power_df
    elif days == 'Weekdays':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        power_df_filtered = power_df[power_df['weekday'].astype(str).str.contains('6|7')]
    
    if subject_id is not None:
        sub_clean = subject_id.lower().replace('_','').replace('qualr','PCX-PCR').replace('qualm','PCX-PCM')
        sub = f'sub-{sub_clean}'
        df = power_df_filtered.query("subject_id == @sub")
    else:
        df = power_df_filtered
    fig = px.line(df, x='day', y='daily_mins', color='subject_id', title=f'Phone Activity (minutes each hour) for {sub}', 
                  height=400, width=600)
    return fig


# Add controls to build the interaction
@callback(
    Output(component_id='activity-graph', component_property='figure'),
    Input(component_id='subject-id', component_property='data'),
    Input(component_id='days', component_property='value')
)

def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    if subject_id is None:
        return None
    sub_clean = subject_id.lower().replace('_','').replace('qualr','PCX-PCR').replace('qualm','PCX-PCM')
    sub = f'sub-{sub_clean}'
    sub_df = accel_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Physical Activity (acceleration speed) minutes each hour for {sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig



@callback(
    Output(component_id='gps-graph', component_property='figure'),
    Input(component_id='subject-id', component_property='data'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    if subject_id is  None:
        return None
    sub_clean = subject_id.lower().replace('_','').replace('qualr','PCX-PCR').replace('qualm','PCX-PCM')
    sub = f'sub-{sub_clean}'
    sub_df = gps_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Mobility (distance each hour) for {sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig



