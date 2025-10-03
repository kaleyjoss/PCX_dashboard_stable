import dash
from dash import html, Input, Output, callback, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, _dash_renderer, dash_table
from dash_iconify import DashIconify
_dash_renderer._set_react_version("18.2.0")
import logging
import os
import sys
import dash
from dash import html, dcc, callback, Input, Output
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import re
import pickle
import inspect
import datetime
from datetime import datetime as dt
import numpy as np

dash.register_page(__name__, 
    path='/', # these 3 are automatically generated like this, but you can edit them
    title='Home',
    name='Home'
)

# # Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)

# Set up logging
logging.basicConfig(
    filename='dashboard.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.sub_id import extract
from scripts.paths import load_paths
from scripts.surveys import load_surveys, add_diagnoses_columns

paths = load_paths()
project_dir = paths["project_dir"]
surveys_dir = paths["surveys_dir"]
rmr_df = paths["rmr_df"]
tracker_df = paths["tracker_df"]
demographic_df_dir = paths["demographic_df_dir"]

surveys, recoded_surveys = load_surveys(surveys_dir)
surveys = add_diagnoses_columns(surveys)

first_df = surveys['clinical_administered_data']
subject_ids = first_df['SUBJECT_ID'].unique()

#RMR visual
session1 = surveys['clinical_administered_data']
print(f'session1 head:: len {len(session1)}')
print(session1.head())
print('session1 head::')

session2 = surveys['mri_self_report_data']
session1sr = surveys['clinical_self_report_data']
session3 = surveys['supplemental_self_report_data']

session1['duration_mins'] = pd.to_numeric(session1['Duration (in seconds)'])/60
session1_r = session1[session1['SITE_ID']=='Rutgers University / UBHC']
session1_m = session1[session1['SITE_ID'] == 'McLean Hospital']

session1sr['duration_mins'] = pd.to_numeric(session1sr['Duration (in seconds)'])/60
session1sr_r = session1sr[session1sr['SITE_ID']=='Rutgers University / UBHC']
session1sr_m = session1sr[session1sr['SITE_ID'] == 'McLean Hospital']

session2['duration_mins'] = pd.to_numeric(session2['Duration (in seconds)'])/60
session2_r = session2[session2['SITE_ID']=='Rutgers University / UBHC']
session2_m = session2[session2['SITE_ID'] == 'McLean Hospital']

total_real = len(session1_r) + len(session1_m)

# Pie charts
primary_pie = px.pie(session1, names='primary_diagnoses_all', title='Subject Primary Diagnoses')
other_pie = px.pie(session1, names='other_diagnoses_all', title='Subject Other Diagnoses')


survey_cols = [
    "SUBJECT_ID",'SITE_ID','primary_diagnoses_all','other_diagnoses_all',
    'clinical_administered_data','clinical_self_report_data', 
    'mri_self_report_data','supplemental_self_report_data',
	"sex","age", "ethnic","racial","place_birth", 'name_meds','purpose_meds']

session0_merge = session1[[col for col in survey_cols if col in session1.columns]]
session1_merge = session1sr[[col for col in survey_cols if col in session1sr.columns]]
session2_merge = session2[[col for col in survey_cols if col in session2.columns]]
session3_merge = session3[[col for col in survey_cols if col in session3.columns]]

# align on SUBJECT_ID first
s1 = session1_merge.set_index("SUBJECT_ID")
s2 = session2_merge.set_index("SUBJECT_ID")
s3 = session3_merge.set_index("SUBJECT_ID")
s0 = session0_merge.set_index("SUBJECT_ID")
demographic_df = s1.combine_first(s2).combine_first(s3).combine_first(s0).reset_index()


demographic_df = (
    demographic_df.groupby("SUBJECT_ID")
    .agg(lambda x: ", ".join(x.dropna().astype(str).unique()))
    .reset_index())
today = datetime.datetime.today()
today_str = today.strftime('%b %d %Y')
demographic_df.to_csv(os.path.join(demographic_df_dir, f'demographic_df_{today_str}.csv'))

rate_per_day = 0.22
start = 'Dec 1 2024'
beginning = dt.strptime(start, '%b %d %Y')
days_of_study = today - beginning
today_goal = int(days_of_study.days * rate_per_day)
today_site = today_goal / 2
today_c = pd.DataFrame([today_str, 'Today', np.nan, np.nan, today_site, today_site, today_goal, len(session1_r), len(session1_r), len(session2_r), len(session1_m), len(session1_m), len(session2_m), total_real])
today_row = today_c.T
today_row.columns = rmr_df.columns.to_list()
rmr_df_today = pd.concat([rmr_df, today_row])
rmr_df_today['Date'] = rmr_df_today['Date'].apply(lambda x: dt.strptime(x, '%b %d %Y'))
rmr_df_today = rmr_df_today.sort_values('Date').reset_index(drop=True)
rmr_df_today = rmr_df_today.reset_index()
today_row = rmr_df_today.loc[rmr_df_today['Date']==today_str]
today_index = today_row['index'].values.squeeze()
two_quarters_out=today_index+2
rmr_df_today = rmr_df_today[:two_quarters_out]

rmr_goal = px.line(rmr_df_today, x='Date', y=['Total Goal', 'Total Real'], width=500, height=300, title='Total Subjects Consented: Goal and Real', labels='Quarter')
r_goal = px.line(rmr_df_today, x='Date', y=['Rutgers Goal', 'Rutgers Consented', 'Rutgers Clinical Interview', 'Rutgers Scan'], width=500, height=300, title='Subjects at Rutgers vs. Goal', labels='Quarter')
m_goal = px.line(rmr_df_today, x='Date', y=['McLean Goal', 'McLean Consented', 'McLean Clinical Interview', 'McLean Scan'], width=500, height=300, title='Subjects at McLean vs. Goal', labels='Quarter')



# # Surveys
# cad_recoded = recoded_surveys['clinical_administered_data'][2:]
# panss_p_total_cols = [f'panss_p0{str(i)}' for i in range(1,8)]
# panss_n_total_cols = [f'panss_n0{str(i)}' for i in range(1,8)]
# panss_g_total_cols = [f'panss_g0{str(i)}' for i in range(1,8)]
# bprs_total_cols = [f'bprs_0{str(i)}' for i in range(1,10)]+[f'bprs_1{i}' for i in range(0,9)]
# ymrs_total_cols = [f'ymrs_0{str(i)}' for i in range(1,10)]+[f'ymrs_1{i}' for i in range(0,2)]
# madrs_total_cols = [f'madrs_0{str(i)}' for i in range(1,10)]+['madrs_10']

# all_cols = panss_p_total_cols+panss_n_total_cols+panss_g_total_cols+bprs_total_cols+ymrs_total_cols+madrs_total_cols
# cad_recoded[all_cols] = cad_recoded[all_cols].astype(float)


# cad_recoded['panss_p_total'] = cad_recoded[panss_p_total_cols].sum(axis=1)
# cad_recoded['panss_n_total'] = cad_recoded[panss_n_total_cols].sum(axis=1)
# cad_recoded['panss_g_total'] = cad_recoded[panss_g_total_cols].sum(axis=1)
# cad_recoded['bprs_total'] = cad_recoded[bprs_total_cols].sum(axis=1)
# cad_recoded['ymrs_total'] = cad_recoded[ymrs_total_cols].sum(axis=1)
# cad_recoded['madrs_total'] = cad_recoded[madrs_total_cols].sum(axis=1)




# Tracker Visual
subs_df = paths['tracker_df']
subs_df_binary = subs_df.fillna(0)
subs_df_filtered = subs_df_binary.loc[subs_df_binary['Clinical Interview Session Date'] != 0, :]
subs_df_filtered = subs_df_filtered.loc[:, ~subs_df_filtered.columns.str.contains('Unnamed', case=False)]
tags_row = subs_df_filtered.iloc[0]

def filter_by_tag(df, tags_row, desired_tags):
    matching_cols = []
    for tag in desired_tags:
        matching = tags_row[tags_row.astype(str).str.contains(tag, na=False)].index.tolist()
        matching_cols.extend(matching)

    # Remove duplicates while preserving order
    matching_cols = list(dict.fromkeys(matching_cols))

    return df[matching_cols]

tracker_df = filter_by_tag(subs_df_filtered, tags_row, ['id','tracker'])

# # Now the structure is:
# # |PCR ID:  | SUBJECT_ID |     Session Date    |   Session Time     | <-- these are all columns in tracker
# # |tags     |  id     | tracker, scheduling | tracker, scheduling| ...
# # |PCR200   |qualr200 |     <value>         |       <value>      | ...


icons = {
    'up': "tabler:arrow-up-right",
    'down': "tabler:arrow-down-right",
}


r_prog = int((len(session1_r)/135)*100)
r_scans_prog = int((len(session2_r)/135)*100)
m_prog = int((len(session1_m)/135)*100)
m_scans_prog = int((len(session2_m)/135)*100)

data = [
    {'label': 'Rutgers Clinical Interview', 'stats': len(session1_r), 'progress': r_prog, 'color': 'red', 'icon': 'up'},
    {'label': 'Rutgers Scans', 'stats': len(session2_r), 'progress': r_scans_prog, 'color': 'red', 'icon': 'up'},
    {'label': 'McLean Clinical Interview', 'stats': len(session1_m), 'progress': m_prog, 'color': 'blue', 'icon': 'up'},
    {'label': 'McLean Scans', 'stats': len(session2_m), 'progress': m_scans_prog, 'color': 'blue', 'icon': 'up'},
]



def StatsRing():
    stats = []
    for stat in data:
        Icon = icons[stat['icon']]
        stats.append(
            dmc.Paper(
                children=[
                    dmc.Group(
                        children=[
                            dmc.RingProgress(
                                size=80,
                                roundCaps=True,
                                thickness=8,
                                sections=[{'value': stat['progress'], 'color': stat['color']}],
                                label=dmc.Center(
                                    DashIconify(icon=Icon, width=20, height=20)
                                )
                            ),
                            dmc.Box(
                                children=[
                                    dmc.Text(stat['label'], c="dimmed", size="xs", tt="uppercase", fw=700),
                                    dmc.Text(stat['stats'], fw=700, size="xl"),
                                ]
                            )
                        ]
                    )
                ],
                withBorder=True,
                radius="md",
                p="xs",
            )
        )

    return dmc.SimpleGrid(
        children=stats,
        cols={"base": 4, "sm": 1},
        p="lg"
    )



def render_table(df, cols):
    if 'SUBJECT_ID' not in cols:
        cols = cols + ['SUBJECT_ID']
    survey_df = df[cols]

    return dash_table.DataTable(
        data=survey_df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in survey_df.columns],
        css=[{
            "selector": ".dash-spreadsheet td div",
            "rule": """
                line-height: 20px;
                max-height: none; min-height: 20px; height: auto;
                display: block;
                white-space: normal;
                overflow-y: visible;
            """
            }],
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in survey_df.to_dict('records')
        ],
        tooltip_duration=None,
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "fontFamily": "Arial, sans-serif",
            "fontSize": "14px",
            "padding": "8px"
        },
        style_header={
            "backgroundColor": "#f0f2f6",
            "fontWeight": "bold"
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fafafa"
            }
        ]      
    )


#recent_subs = render_table()

# App layout
layout = html.Div([
    dmc.MantineProvider(children=[
        dmc.Text('PCX Current Status',  c='blue', tt='uppercase',style={"fontSize": 40},),
        StatsRing(),
        html.Div(render_table(demographic_df, survey_cols)),
        dmc.Group(id='graphs', children=[
            dcc.Graph(figure=rmr_goal, id='rmr-goal'),
            dcc.Graph(figure=r_goal, id='rutgers-goal'),
            dcc.Graph(figure=m_goal, id='mclean-goal'),
            html.Div(id='graphs', children=[
                dcc.Graph(figure=primary_pie, id='primary-pie'),
                dcc.Graph(figure=other_pie, id='other-pie'),
                ]),
            ]),
            #html.Div(figure=recent_subs, id='recent-subs', style={'width': '20%', 'padding': '0px'}),

        # html.Div(id='duration-container', children=[
		# 		dcc.RadioItems((['Rutgers', 'McLean']), id='site', value='Rutgers'),
        #         dcc.Tabs(id="session", value='Clinical Interview Session', children=[
        #             dcc.Tab(label='Clinical Interview Session', value='Clinical Interview Session'),
		# 			dcc.Tab(label='Clinical Self-Report', value='Clinical Self-Report'),
        #             dcc.Tab(label='fMRI Self-Report', value='fMRI Self-Report'),
		# 		]),

		# 		html.Div(id='table-duration', style={'width': 500,'padding': '5px'}),
        #         html.Div(id='chart-duration', style={'width': 500,'padding': '5px'})
		# ]),

    ]),
    
    # dcc.Graph(figure={}, id='dashboard-graph', style={
    #     'width': '100%',
    #     'height': '100%',
    #     'padding': 10,
    #     'flex': 1,})
    
])



# Controls to filter the figure by subject ID and
@callback(
    Output('dashboard-graph', 'figure'),
    Input('subject-id', 'data')
)

def cb(subject_id):
    if subject_id is None:
        filtered_df = tracker_df
    else:
        filtered_df = tracker_df[tracker_df['SUBJECT_ID'] == subject_id]
    
    # Binarize non-zero values
    filtered_df_bin = filtered_df.where(filtered_df == 0, 1)
    #display(filtered_df_bin)
    
    # Create the figure
    fig = px.imshow(filtered_df_bin, origin='lower',
                    title="Tasks Completed by Participants",
                    zmin=0, zmax=1, color_continuous_scale=[[0, "white"], [1, "black"]],
                    labels=dict(x="Tasks Completed", y="Subject", color="Done = Black"),
                    x=filtered_df.columns,
                    y=filtered_df['SUBJECT_ID'],
                    width=1500, height=800)
    return fig


# @callback(
#     Output('table-duration', 'children'),
#     Output('chart-duration', 'children'),
#     Input('site', 'value'),
#     Input('session', 'value'),
# )

# def cb(site, session):
#     if session=='Clinical Interview Session':
#         if site=='McLean':
#             df = session1_m
#         else:
#             df = session1_r
#     if session=='Clinical Self-Report':
#         if site=='McLean':
#             df = session1sr_m
#         else:
#             df = session1sr_r
#     if session=='fMRI Self-Report':
#         if site=='McLean':
#             df = session2_m
#         else:
#             df = session2_r
#     cols = ['SUBJECT_ID','RecordedDate', 'duration_mins','primary_diagnoses_all', 'other_diagnoses_all']
#     cols_present = [col for col in cols if col in df.columns]


    
#     #Bar chart of duration for each sub
#     fig = px.bar(df, x='SUBJECT_ID', y='duration_mins', text_auto='.2s', range_y=[0,120])

#     return render_table(df, cols_present), dcc.Graph(figure=fig,config={'displayModeBar': True},style={'width': 500,  'height': 300},  className = "outer-graph")
