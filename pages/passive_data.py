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
from dash import Dash, html, dcc, Input, Output, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os
import glob

# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.update_dataframes import update_dfs
from scripts.paths import load_paths
from scripts.surveys_loader import load_surveys

# Register page into dash app as pagename
dash.register_page(__name__, path="/passive_data", title='Passive Data', name='Passive Data')

sensor_to_file_dict = {'gps': ['gps_freq','gps_freq2','gps_dist'],
                       'accel': ['accel_activityScores'],
                       'power': ['power_activityScores']}


# === Paths ===
paths_dict = load_paths()
pcx_dir = paths_dict["pcx_dir"]
mindlamp_dir = paths_dict['mindlamp_dir']
DATA_DIR = os.path.join(mindlamp_dir, 'data')


# === Layout ===
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Participant Dashboard"),
            html.Hr(),
            html.Div(id='data-status', className='text-muted')
        ], width=3),

        dbc.Col([
            dcc.Tabs(id='tabs', value='tab-data', children=[
                dcc.Tab(label='Heatmap', value='tab-data'),
                dcc.Tab(label='Figures', value='tab-figs'),
            ]),
            html.Div(id='tab-content', style={'marginTop': 20}),
            dcc.Checklist(id='survey-cols', value=['Cheerful'], options=['Cheerful', 'Stressed', 'Down', 'Relaxed', 'Down', 'Strange', 'Content', 'Suspicious', 'Relaxed', 'Racing', 'Enthusiastic', 'Auditory', 'Empty', 'Anxious', 'Concentrate', 'Irritable', 'Confused', 'Visual', 'Handle', 'Function', 'Socialp', 'Sociald','Negative','Positive'],inline=True, style={'marginTop': 10, 'marginLeft': 10, 'marginRight': 10}),
            html.Div(id='survey-graph'),
            html.Div(id='survey-msgs')
        ], width=9)
    ])
], fluid=True)


@callback(
    Output('tab-content', 'children'),
    Output('data-status', 'children'),
    Input(component_id='subject-id', component_property='data'),
    Input('tabs', 'value'),

)
def update_tab(subject_id, active_tab):
    if not subject_id:
        return "Please select a participant.", "⚠️ No subject selected."
    if 'qual' in subject_id:
        subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

    subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
    if not os.path.exists(subj_path):
        return html.Div(f"No sensor activity data found. Looked in {subj_path} "), f"❌ No data in {subj_path}"

    # ---- Tab 1: HEATMAP ----
    if active_tab == 'tab-data':
        figs = []
        status_msgs = []
        for sensor in sensor_to_file_dict:
            for file in sensor_to_file_dict[sensor]:
                path = f'{os.path.join(subj_path, sensor)}'
                if not os.path.exists(path):
                    status_msgs.append(f"❌ {sensor}: folder missing")
                    continue
                
                csvs = glob.glob(os.path.join(path, f"**{file}**.csv"))
                if not csvs:
                    status_msgs.append(f"⚠️ {sensor}: no CSVs")
                    continue

                df = pd.read_csv(sorted(csvs)[-1])  # take latest
                num_df = df[[col for col in df.columns if 'activityScore' in col]]
                # Drop empty rows/days, this happens bc participants start some time after start of study
                num_df_clean = num_df.dropna(axis=0, how='all')
                
                if num_df_clean.empty:
                    status_msgs.append(f'{file} exists but no data has been collected.')
                    continue
                
                status_msgs.append(f'Found {file} csv')

                
                fig = px.imshow(
                    num_df_clean.values,
                    origin='lower',
                    color_continuous_scale='Viridis',
                    labels={'x': "Hour of Day", 'y': "Day"},
                    title=f"{file.capitalize()})"
                )
                fig.update_layout(
                    height=400, width=300,
                    margin=dict(l=10, r=10, t=30, b=30),
                    coloraxis_showscale=False
                )
                figs.append(dcc.Graph(figure=fig, style={'margin': '15px'}))

        if not figs:
            return html.Div(f"No sensor activity data found. Looked in {subj_path} "), f"{status_msgs} ⚠️ No data to show"

        grid = html.Div(
            figs,
            style={
                'display': 'flex',
                'flexWrap': 'wrap',
                'justifyContent': 'center',
                'gap': '10px'
            }
        )
        return grid, html.Ul([html.Li(msg) for msg in status_msgs])


    # ---- Tab 3: FIGURES ----
    elif active_tab == 'tab-figs':
        fig_dir = os.path.join(subj_path, 'mtl_plt')
        imgs = [f for f in os.listdir(fig_dir) if f.endswith('.png')]
        if not imgs:
            return html.Div("No images available."), f"⚠️ No .png figures from {fig_dir}"
        return html.Div([
            html.Div([
                html.Img(src=f"/{fig_dir}/{img}", style={'width': '90%', 'margin': '10px'})
                for img in imgs
            ], style={'display': 'flex', 'flexWrap': 'wrap'})
        ]), f"Showing {len(imgs)} figures."


@callback(
    Output(component_id='survey-graph', component_property='children'),
    Output(component_id='survey-msgs', component_property='children'),
    Input(component_id='subject-id', component_property='data'),
    Input('survey-cols', 'value'),   
)
def update_survey(subject_id, survey_cols):
    if not subject_id:
        return "Please select a participant.", "⚠️ No subject selected."
    if 'qual' in subject_id:
        subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

    subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
    if not os.path.exists(subj_path):
        return html.Div("No data found for this sensor."), f"❌ No data in {subj_path}"

    survey_path = os.path.join(subj_path, 'survey')
    csvs = glob.glob(os.path.join(survey_path, f"**surveyAnswers_activityScores**.csv"))
    if not csvs:
        return html.Div("No survey data found."), f"⚠️ No survey CSVs from {survey_path}"
    df = pd.read_csv(sorted(csvs)[-1])
    if 'day' in df.columns:
        df['day'] = pd.to_numeric(df['day'], errors='coerce')
    else:
        return html.Div(f"Survey {os.path.basename(csvs[-1])} had no 'day' column"), f"Survey {os.path.basename(csvs[-1])} had no 'day' column"
    fig = px.line(df, x='day', y=survey_cols, title=f'Subject {subject_id} Survey Responses')
    return dcc.Graph(figure=fig), f"✅ Survey: {os.path.basename(csvs[-1])}"

