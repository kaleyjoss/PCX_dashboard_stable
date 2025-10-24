from locale import D_FMT
import os
import sys
import re
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
from pages.home import demographic_df_dir
import pandas as pd
import xarray as xr
import importlib
import logging
import pickle
import os
import sys
import inspect
import dash_mantine_components as dmc
from pathlib import Path
from datetime import datetime as dt 
from datetime import timedelta
# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
from scripts.paths import load_paths
import scripts.sub_id as sub_id
from scripts.surveys_loader import load_surveys
from scripts.tables import render_demographic_df
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])


# Register page into dash app as pagename
dash.register_page(__name__, path="/sub_table", title='Subjects Table', name='Subjects Table')

paths_dict = load_paths()
demographic_df_dir = Path(paths_dict['demographic_df_dir'])
demographic_df_path = max(demographic_df_dir.glob("*.csv"), key=lambda f: f.stat().st_mtime)
demographic_df = pd.read_csv(demographic_df_path)
demographic_df["clinical_administered_data"] = pd.to_datetime(demographic_df["clinical_administered_data"], errors="coerce")
demographic_df["mri_self_report_data"] = pd.to_datetime(demographic_df["mri_self_report_data"], errors="coerce")

# Time variables
today_str = dt.now().strftime('%Y-%m-%d')
two_weeks_ago = dt.now() - timedelta(weeks=2)
two_weeks_ago_str = two_weeks_ago.strftime('%Y-%m-%d')
one_month_ago = dt.now() - timedelta(weeks=4)
one_month_ago_str = one_month_ago.strftime('%Y-%m-%d')


survey_cols = [
    "SUBJECT_ID",'SITE_ID','primary_diagnoses_all','other_diagnoses_all',
    'clinical_administered_data', 'mri_self_report_data','supplemental_self_report_data', 
    'MADRS_category','YMRS_category', 'PANSS_Positive_Category','PANSS_Negative_Category','PANSS_General_Category','PANSS_Total_category',
	"sex","age", "ethnic","racial","place_birth", 'name_meds','purpose_meds','panss_total', 'panss_p_total','panss_n_total','panss_g_total', 'bprs_total','ymrs_total','madrs_total',]

display_survey_cols = [col for col in survey_cols if 'total' not in col and 'Category' not in col and 'supplemental' not in col]



layout = html.Div([
    dmc.MantineProvider(children=[
        dmc.Text(f'All Subject sessions ({len(demographic_df)} subjects)',  c='blue',style={"fontSize": 30})
    ]),
    dcc.RadioItems(
            id='site',
            options=[
                {'label': 'Rutgers', 'value': 'Rutgers'},
                {'label': 'McLean', 'value': 'McLean'},
            ],
            value='Rutgers',  # default selected
            inline=True      # makes checkboxes horizontal
        ),
    dcc.RadioItems(
            id='timeframe',
            options=[
                {'label': 'All Subjects', 'value': 'all'},
                {'label': 'Past Month', 'value': 'month'},
                {'label': 'Past 2 weeks', 'value': 'weeks'},
            ],
            value='all',  # default selected
            inline=True      # makes checkboxes horizontal
        ),
    html.Div(id='subs-table'),
    html.Div(render_demographic_df(demographic_df, display_survey_cols)),
])

@callback(
    Output('subs-table', 'children'),
    Input('site', 'value'),
    Input('timeframe', 'value'),
)

def cb(site, timeframe):
    df = demographic_df
    if site == 'Rutgers':
        df = df[df['SITE_ID']=='Rutgers']
    
    if site == 'McLean':
         df = df[df['SITE_ID']=='McLean']

    if timeframe == 'month':
        recent_clin = df[df['clinical_administered_data'] >= one_month_ago]
        recent_mri = df[df['mri_self_report_data'] >= one_month_ago]
        df = pd.concat([recent_clin, recent_mri])
        df = df.drop_duplicates()
        return render_demographic_df(df, display_survey_cols)
    
    if timeframe == 'month':
        df = df[
            (df['clinical_administered_data'] >= one_month_ago) |
            (df['mri_self_report_data'] >= one_month_ago)
        ]
    elif timeframe == 'weeks':
        df = df[
            (df['clinical_administered_data'] >= two_weeks_ago) |
            (df['mri_self_report_data'] >= two_weeks_ago)
        ]        
        
    df = df.drop_duplicates()
    return render_demographic_df(df, display_survey_cols)


