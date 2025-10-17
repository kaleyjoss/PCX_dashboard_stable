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
from scripts.surveys import load_surveys

# Register page into dash app as pagename
dash.register_page(__name__, path="/passive_data", title='Passive Data', name='Passive Data')

# === Paths ===
paths_dict = load_paths()
pcx_dir = paths_dict["pcx_dir"]
mindlamp_dir = paths_dict['mindlamp_dir']
DATA_DIR = os.path.join(mindlamp_dir, 'data')
sensor_dirs = ['accel', 'gps', 'power', 'survey']
# === Layout ===
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Participant Dashboard"),
            dcc.RadioItems(
                id='sensor',
                options=sensor_dirs,
                value='power',
                inline=True
            ),
            html.Hr(),
            html.Div(id='data-status', className='text-muted')
        ], width=3),

        dbc.Col([
            dcc.Tabs(id='tabs', value='tab-data', children=[
                dcc.Tab(label='Heatmap', value='tab-data'),
                dcc.Tab(label='Survey', value='tab-survey'),
                dcc.Tab(label='Figures', value='tab-figs'),
            ]),
            html.Div(id='tab-content', style={'marginTop': 20})
        ], width=9)
    ])
], fluid=True)


@callback(
    Output('tab-content', 'children'),
    Output('data-status', 'children'),
    Input(component_id='subject-id', component_property='data'),
    Input('sensor', 'value'),
    Input('tabs', 'value')
)
def update_tab(subject_id, sensor, active_tab):
    if not subject_id:
        return "Please select a participant.", "⚠️ No subject selected."
    if 'qual' in subject_id:
        subject_id = subject_id.replace('qualr','PCR').replace('qualm','PCM')

    subj_path = os.path.join(DATA_DIR, subject_id, 'phone', 'processed')
    if not os.path.exists(subj_path):
        return html.Div("No data found for this sensor."), f"❌ No data for {sensor}. Looking in {subj_path}"

    # ---- Tab 1: HEATMAP ----
    if active_tab == 'tab-data':
        figs = []
        status_msgs = []
        for sensor in sensor_dirs:
            path = os.path.join(subj_path, sensor)
            if not os.path.exists(path):
                status_msgs.append(f"❌ {sensor}: folder missing")
                continue

            csvs = glob.glob(os.path.join(path, f"*{sensor}*activityScores*.csv"))
            if not csvs:
                status_msgs.append(f"⚠️ {sensor}: no activityScores CSVs")
                continue

            df = pd.read_csv(sorted(csvs)[-1])  # take latest
            num_df = df.select_dtypes(include='number')

            if num_df.empty:
                status_msgs.append(f"⚠️ {sensor}: no numeric data")
                continue

            fig = px.imshow(
                num_df.values,
                origin='lower',
                color_continuous_scale='Viridis',
                labels={'x': "Hour of Day", 'y': "Day"},
                title=f"{sensor.capitalize()} activity ({os.path.basename(csvs[-1])})"
            )
            fig.update_layout(
                height=300, width=300,
                margin=dict(l=30, r=30, t=50, b=30),
                coloraxis_showscale=False
            )
            figs.append(dcc.Graph(figure=fig, style={'margin': '5px'}))
            status_msgs.append(f"✅ {sensor}: loaded {os.path.basename(csvs[-1])}")

        if not figs:
            return html.Div("No sensor activity data found."), "⚠️ No data to show"

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


    # ---- Tab 2: SURVEY ----
    elif active_tab == 'tab-survey':
        survey_path = os.path.join(subj_path, 'survey')
        csvs = glob.glob(os.path.join(survey_path, f"*surveyAnswers_activityScores*.csv"))
        if not csvs:
            return html.Div("No survey data found."), f"⚠️ No survey CSVs from {survey_path}"
        df = pd.read_csv(sorted(csvs)[-1])
        fig = px.line(df, x='day', y=['Cheerful', 'Stressed', 'Down', 'Relaxed'])
        return dcc.Graph(figure=fig), f"✅ Survey: {os.path.basename(csvs[-1])}"

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
        ]), f"🖼️ Showing {len(imgs)} figures."

